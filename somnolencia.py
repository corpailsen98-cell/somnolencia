import cv2
import numpy as np
import mediapipe as mp
import math
import time
import threading
from typing import Tuple, Dict
import pygame
from dataclasses import dataclass

import mysql.connector
from datetime import datetime

# -----------------------
# Conexión a la base de datos (ajusta usuario/clave si hace falta)
# -----------------------
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",        # <-- pon tu contraseña si tienes
        database="somnolencia"
    )
    cursor = conn.cursor()
    print("✅ Conexión MySQL OK")
except Exception as e:
    conn = None
    cursor = None
    print("⚠️ No se pudo conectar a MySQL:", e)

# -----------------------
# Métricas y dataclass
# -----------------------
@dataclass
class DrowsinessMetrics:
    blinks_count: int = 0
    head_nods_count: int = 0      # Contador de cabeceos
    yawns_count: int = 0          # Contador de bostezos
    eye_closed_time: float = 0.0
    last_blink_time: float = 0.0
    drowsiness_level: str = "ALERTA"
    ear_left: float = 0.0
    ear_right: float = 0.0
    head_pose: Dict[str, float] = None
    is_face_detected: bool = False
    mouth_open_ratio: float = 0.0

    def __post_init__(self):
        if self.head_pose is None:
            self.head_pose = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

# -----------------------
# Detector principal
# -----------------------
class DrowsinessDetector:
    def __init__(self,
                 ear_threshold: float = 0.25,
                 drowsy_time_threshold: float = 1.5,
                 microsleep_threshold: float = 3.0,
                 yawn_threshold: float = 0.60):
        # MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

        # Landmarks
        self.LEFT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
        self.MOUTH_OUTER = [61, 291, 13, 14]

        # Umbrales
        self.ear_threshold = ear_threshold
        self.drowsy_time_threshold = drowsy_time_threshold
        self.microsleep_threshold = microsleep_threshold
        self.yawn_threshold = yawn_threshold

        # Estado
        self.metrics = DrowsinessMetrics()
        self.eye_closed_start_time = None
        self.is_blinking = False
        self.is_yawning = False

        # Para contar cabeceos correctamente (estado máquina)
        self._was_nodding = False   # estado previo: ¿estaba cabeceando?
        self._is_nodding = False    # estado actual temporal
        self.nod_debounce_time = 0.6  # tiempo mínimo entre detección y aceptación (s)
        self._last_nod_time = 0.0

        # Calibración
        self.baseline_y_diff = None
        self.baseline_nose_y = None
        self.calibration_frames = 0
        self.is_calibrated = False

        # Audio
        self._init_audio_system()
        self.alert_thread = None
        self.stop_alert = threading.Event()
        self.alert_active = False

    # ---------------- Audio ----------------
    def _init_audio_system(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_available = True
            print("✅ Audio inicializado")
        except Exception as e:
            print("⚠️ No se pudo inicializar pygame.mixer:", e)
            self.audio_available = False

    def _beep_once(self, frequency=1000, duration=0.3):
        if not self.audio_available:
            return
        try:
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            for i in range(frames):
                wave = 0.35 * np.sin(2 * np.pi * frequency * i / sample_rate)
                arr[i] = [wave, wave]
            arr = (arr * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
        except Exception:
            pass

    def _play_alert_sound_loop_once(self):
        if not self.audio_available:
            return
        try:
            duration = 0.5
            sample_rate = 22050
            frequency = 700
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            for i in range(frames):
                wave = 0.3 * np.sin(2 * np.pi * frequency * i / sample_rate)
                arr[i] = [wave, wave]
            arr = (arr * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
        except Exception:
            pass

    def _start_alert_sequence(self):
        if self.alert_thread and self.alert_thread.is_alive():
            return
        self.stop_alert.clear()
        self.alert_thread = threading.Thread(target=self._alert_loop, daemon=True)
        self.alert_thread.start()

    def _alert_loop(self):
        while not self.stop_alert.is_set():
            self._play_alert_sound_loop_once()
            time.sleep(0.8)

    def _stop_alert_sequence(self):
        self.stop_alert.set()
        if self.alert_thread:
            self.alert_thread.join(timeout=1.0)

    # ---------------- Cálculos ----------------
    def _calculate_ear(self, eye_landmarks, landmarks):
        try:
            pts = []
            for idx in eye_landmarks:
                lm = landmarks.landmark[idx]
                pts.append([lm.x, lm.y])
            pts = np.array(pts)
            v1 = np.linalg.norm(pts[1] - pts[5])
            v2 = np.linalg.norm(pts[2] - pts[4])
            h = np.linalg.norm(pts[0] - pts[3])
            return (v1 + v2) / (2.0 * (h + 1e-8))
        except Exception:
            return 0.0

    def _calculate_mouth_ratio(self, landmarks):
        try:
            left = landmarks.landmark[self.MOUTH_OUTER[0]]
            right = landmarks.landmark[self.MOUTH_OUTER[1]]
            top = landmarks.landmark[self.MOUTH_OUTER[2]]
            bottom = landmarks.landmark[self.MOUTH_OUTER[3]]
            horizontal = math.hypot(right.x - left.x, right.y - left.y)
            vertical = math.hypot(bottom.x - top.x, bottom.y - top.y)
            return vertical / (horizontal + 1e-6)
        except Exception:
            return 0.0

    def _detect_head_pose(self, landmarks) -> Dict[str, float]:
        try:
            nose_tip = landmarks.landmark[1]
            left_eye = landmarks.landmark[33]
            right_eye = landmarks.landmark[362]
            left_mouth = landmarks.landmark[61]
            right_mouth = landmarks.landmark[291]
            eye_center_x = (left_eye.x + right_eye.x) / 2
            mouth_center_x = (left_mouth.x + right_mouth.x) / 2
            yaw = (mouth_center_x - eye_center_x) * 100
            eye_center_y = (left_eye.y + right_eye.y) / 2
            pitch = (nose_tip.y - eye_center_y) * 100
            eye_angle = math.atan2(right_eye.y - left_eye.y, right_eye.x - left_eye.x)
            roll = math.degrees(eye_angle)
            return {"pitch": pitch, "yaw": yaw, "roll": roll}
        except Exception:
            return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

    # ---------------- Calibración y detección de cabeceo ----------------
    def _calibrate_baseline(self, landmarks):
        if self.is_calibrated:
            return
        frente = landmarks.landmark[10]
        barbilla = landmarks.landmark[152]
        nariz = landmarks.landmark[1]
        y_diff = abs(frente.y - barbilla.y)
        nose_y_relative = nariz.y - frente.y
        if self.baseline_y_diff is None:
            self.baseline_y_diff = y_diff
            self.baseline_nose_y = nose_y_relative
        else:
            self.baseline_y_diff = (self.baseline_y_diff + y_diff) / 2
            self.baseline_nose_y = (self.baseline_nose_y + nose_y_relative) / 2
        self.calibration_frames += 1
        if self.calibration_frames >= 30:
            self.is_calibrated = True
            print("✅ Calibración completada")

    def _check_head_nod_position(self, landmarks) -> bool:
        """
        Retorna True si la cabeza está en posición 'normal' (NO cabeceando).
        Actualiza contador de cabeceos solo cuando un cabeceo se completa (debounce).
        """
        try:
            self._calibrate_baseline(landmarks)
            if not self.is_calibrated:
                return True

            frente = landmarks.landmark[10]
            barbilla = landmarks.landmark[152]
            nariz = landmarks.landmark[1]

            current_y_diff = abs(frente.y - barbilla.y)
            current_nose_y = nariz.y - frente.y

            y_diff_change = (self.baseline_y_diff - current_y_diff) / (self.baseline_y_diff + 1e-6)
            nose_y_change = (current_nose_y - self.baseline_nose_y) / (abs(self.baseline_nose_y) + 1e-6)

            y_nod = y_diff_change > 0.3
            nose_nod = nose_y_change > 0.5
            is_nodding_now = y_nod or nose_nod

            # Máquina de estados: contamos al terminar el cabeceo (was nodding -> now not nodding)
            now_ts = time.time()
            if is_nodding_now:
                # Registramos comienzo del cabeceo si antes no lo estaba
                if not self._is_nodding:
                    self._is_nodding = True
                    # marca de tiempo inicio
                    self._last_nod_time = now_ts
            else:
                # Si antes estaba cabeceando y ahora terminó -> contamos 1 cabeceo si supera debounce
                if self._is_nodding:
                    # Verificar duración mínima para evitar ruidos
                    dur = now_ts - self._last_nod_time
                    if dur > 0.15:  # filtro mínimo de duración de cabeceo
                        self.metrics.head_nods_count += 1
                        # beep en múltiplos de 3
                        if self.metrics.head_nods_count % 3 == 0:
                            self._beep_once()
                        # INSERT DB al detectar un cabeceo completo
                        try:
                            if cursor is not None:
                                sql = "INSERT INTO viaje (hora_viaje, parpadeo, cabeceos, bosteso) VALUES (%s, %s, %s, %s)"
                                vals = (datetime.now(), self.metrics.blinks_count, self.metrics.head_nods_count, self.metrics.yawns_count)
                                cursor.execute(sql, vals)
                                conn.commit()
                        except Exception as e:
                            print("⚠️ Error insert DB (cabeceo):", e)
                    # reset estado
                    self._is_nodding = False

            self._was_nodding = is_nodding_now
            return not is_nodding_now
        except Exception:
            return True

    # ---------------- Dibujos ----------------
    def _draw_eye_landmarks(self, frame, landmarks):
        h, w = frame.shape[:2]
        for eye_landmarks in [self.LEFT_EYE_LANDMARKS, self.RIGHT_EYE_LANDMARKS]:
            pts = []
            for idx in eye_landmarks:
                lm = landmarks.landmark[idx]
                x = int(lm.x * w); y = int(lm.y * h)
                pts.append((x, y))
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            pts = np.array(pts, np.int32)
            cv2.polylines(frame, [pts], True, (255, 255, 0), 1)

    def _draw_head_landmarks(self, frame, landmarks):
        h, w = frame.shape[:2]
        if not self.is_calibrated:
            cv2.putText(frame, f"CALIBRANDO... {self.calibration_frames}/30",
                        (w - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        head_ok = self._check_head_nod_position(landmarks)
        txt = "Cabeza OK" if head_ok else "CABECEO!"
        color = (0, 255, 0) if head_ok else (0, 0, 255)
        cv2.putText(frame, txt, (w - 220, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        for idx, color, label in [(1, (0, 255, 255), "Nariz"),
                                  (152, (255, 0, 255), "Barbilla"),
                                  (10, (255, 255, 0), "Frente")]:
            lm = landmarks.landmark[idx]
            x = int(lm.x * w); y = int(lm.y * h)
            cv2.circle(frame, (x, y), 4, color, -1)
            cv2.putText(frame, label, (x - 20, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    def _draw_full_face_mesh(self, frame, landmarks):
        self.mp_drawing.draw_landmarks(
            frame,
            landmarks,
            self.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=1)
        )
        self.mp_drawing.draw_landmarks(
            frame,
            landmarks,
            self.mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
            connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=1)
        )

    # ---------------- Procesamiento de frame ----------------
    def process_frame(self, frame) -> Tuple[np.ndarray, DrowsinessMetrics]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        self.metrics.is_face_detected = False

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.metrics.is_face_detected = True

                self.metrics.ear_left = self._calculate_ear(self.LEFT_EYE_LANDMARKS, face_landmarks)
                self.metrics.ear_right = self._calculate_ear(self.RIGHT_EYE_LANDMARKS, face_landmarks)
                avg_ear = (self.metrics.ear_left + self.metrics.ear_right) / 2.0

                head_nod_ok = self._check_head_nod_position(face_landmarks)

                # Bostezo
                mouth_ratio = self._calculate_mouth_ratio(face_landmarks)
                self.metrics.mouth_open_ratio = mouth_ratio
                if mouth_ratio > self.yawn_threshold:
                    if not self.is_yawning:
                        self.is_yawning = True
                        self.metrics.yawns_count += 1
                        # insertar DB al detectar bostezo
                        try:
                            if cursor is not None:
                                sql = "INSERT INTO viaje (hora_viaje, parpadeo, cabeceos, bosteso) VALUES (%s, %s, %s, %s)"
                                vals = (datetime.now(), self.metrics.blinks_count, self.metrics.head_nods_count, self.metrics.yawns_count)
                                cursor.execute(sql, vals)
                                conn.commit()
                        except Exception as e:
                            print("⚠️ Error insert DB (bostezo):", e)
                else:
                    self.is_yawning = False

                # Parpadeo y estados
                current_time = time.time()
                if avg_ear < self.ear_threshold:
                    if not self.is_blinking:
                        self.is_blinking = True
                        self.eye_closed_start_time = current_time
                    else:
                        self.metrics.eye_closed_time = current_time - self.eye_closed_start_time
                        if self.metrics.eye_closed_time > self.microsleep_threshold:
                            self.metrics.drowsiness_level = "MICROSUEÑO"
                            if not self.alert_active:
                                self.alert_active = True
                                self._start_alert_sequence()
                        elif self.metrics.eye_closed_time > self.drowsy_time_threshold:
                            self.metrics.drowsiness_level = "SOMNOLIENTO"
                            if not self.alert_active:
                                self.alert_active = True
                                self._start_alert_sequence()
                        else:
                            self.metrics.drowsiness_level = "NORMAL"
                else:
                    if self.is_blinking:
                        self.is_blinking = False
                        # sólo contar parpadeo si la cabeza no está en cabeceo
                        if head_nod_ok:
                            self.metrics.blinks_count += 1
                            # insertar DB al detectar parpadeo
                            try:
                                if cursor is not None:
                                    sql = "INSERT INTO viaje (hora_viaje, parpadeo, cabeceos, bosteso) VALUES (%s, %s, %s, %s)"
                                    vals = (datetime.now(), self.metrics.blinks_count, self.metrics.head_nods_count, self.metrics.yawns_count)
                                    cursor.execute(sql, vals)
                                    conn.commit()
                            except Exception as e:
                                print("⚠️ Error insert DB (parpadeo):", e)

                        self.metrics.last_blink_time = current_time
                        self.metrics.eye_closed_time = 0.0
                        self.metrics.drowsiness_level = "ALERTA"
                        if self.alert_active:
                            self.alert_active = False
                            self._stop_alert_sequence()

                    if not head_nod_ok:
                        self.metrics.drowsiness_level = "CABECEO_DETECTADO"

                self.metrics.head_pose = self._detect_head_pose(face_landmarks)

                # Dibujos
                self._draw_full_face_mesh(frame, face_landmarks)
                self._draw_eye_landmarks(frame, face_landmarks)
                self._draw_head_landmarks(frame, face_landmarks)
        else:
            self.metrics.drowsiness_level = "SIN_ROSTRO"
            if self.alert_active:
                self.alert_active = False
                self._stop_alert_sequence()

        return frame, self.metrics

    def reset_metrics(self):
        self.metrics = DrowsinessMetrics()
        self.eye_closed_start_time = None
        self.is_blinking = False
        if self.alert_active:
            self._stop_alert_sequence()
            self.alert_active = False

    def cleanup(self):
        self._stop_alert_sequence()
        if self.audio_available:
            pygame.mixer.quit()

# ---------------- Main ----------------
def create_drowsiness_detector(**kwargs) -> DrowsinessDetector:
    return DrowsinessDetector(**kwargs)

if __name__ == "__main__":
    detector = create_drowsiness_detector()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("🔍 Detector de Somnolencia iniciado")
    print("👁️ Cierra los ojos >1.5s para alertas; cabecea para probar el contador")
    print("🔔 Cada 3 cabeceos emite un beep único")
    print("❌ Presiona 'q' para salir")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            processed_frame, metrics = detector.process_frame(frame)

            # HUD
            cv2.putText(processed_frame, f"Parpadeos: {metrics.blinks_count}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(processed_frame, f"Cabeceos: {metrics.head_nods_count}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(processed_frame, f"Bostezos: {metrics.yawns_count}",
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            cv2.putText(processed_frame, f"Estado: {metrics.drowsiness_level}",
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 150, 150), 2)

            if metrics.eye_closed_time > 0:
                cv2.putText(processed_frame, f"Ojos cerrados: {metrics.eye_closed_time:.1f}s",
                            (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 2)
            avg_ear = (metrics.ear_left + metrics.ear_right) / 2.0
            cv2.putText(processed_frame, f"EAR: {avg_ear:.3f}",
                        (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 2)
            cv2.putText(processed_frame, f"Mouth: {metrics.mouth_open_ratio:.3f}",
                        (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 2)

            if detector.alert_active:
                cv2.rectangle(processed_frame, (0, 0), (processed_frame.shape[1], processed_frame.shape[0]),
                              (0, 0, 255), 8)
                cv2.putText(processed_frame, "!!! ALERTA DE SOMNOLENCIA !!!",
                            (processed_frame.shape[1]//2 - 220, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            cv2.imshow("🔍 Detector de Somnolencia - 'q' para salir", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.cleanup()
        print("✅ Detector cerrado correctamente")
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
