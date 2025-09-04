<?php
    include_once("./bdcone.php");

    $usuario = $_POST['txtusuario'];
    $clave = $_POST['txtclave'];

    $query_login = $cadena->prepare("SELECT * FROM user WHERE usuario='$usuario' AND clave='$clave' ");
    $query_login->execute();
    $logines = $query_login->fetchAll(PDO::FETCH_ASSOC);
    foreach($logines as $login){
        $user = $login['usuario'];
        $cla = $login['clave']; 
    }
    if( ($usuario = $user) && ($clave = $cla) )
    {
        /*
        echo "<script>alert('Usuario Correcto');</script>";
        // Ejecuta el script de Python usando la ruta completa
        $output = [];
        $return_var = 0;
        exec("C:\\Users\\USUARIO\\AppData\\Local\\Programs\\Python\\Python310\\python.exe C:\\xampp\\htdocs\\Lista-de-asistencia\\detec_face_mysql.py 2>&1", $output, $return_var);
        // Imprime salida y código de retorno para depuración
        echo "<pre>";
        print_r($output);
        echo "\nCódigo de retorno: $return_var";
        echo "</pre>";
        */
        header('location:./inicio.php');
    } else
    {
        echo "<script> alert('Algo Salio Mal') </script>";
        header('Location: /ilsen/index.html');
    }
?>