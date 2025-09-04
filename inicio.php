<!DOCTYPE html>
<html lang="en">
<head>
  <?php
    include_once("encabezado.php");
  ?>
  <style>
    /* Eliminar los controles */
    .carousel-control-prev, .carousel-control-next {
      display: none; /* Oculta los botones de navegación */
    }

    /* Hacer que las imágenes se ajusten mejor al contenedor */
    .carousel-inner {
      padding-top: 0px; /* Ajusta este valor si necesitas mover las imágenes */
    }

    /* Ajustar la altura del carrusel para que no afecte el diseño */
    .carousel-item img {
      object-fit: cover; /* Esto hace que la imagen se ajuste sin distorsión */
      height: 700px; /* Aumenta la altura de las imágenes */
    }
  </style>
</head>
<body class="hold-transition sidebar-mini layout-fixed">
<div class="wrapper">

  <!-- Navbar -->
  <nav class="main-header navbar navbar-expand navbar-white navbar-light">
    <!-- Left navbar links -->
    <ul class="navbar-nav">
      <li class="nav-item">
        <a class="nav-link" data-widget="pushmenu" href="#" role="button"><i class="fas fa-bars"></i></a>
      </li>
    </ul>
    <!-- Right navbar links -->
  </nav>
  <!-- /.navbar -->

  <!-- Main Sidebar Container -->
  <aside class="main-sidebar sidebar-dark-primary elevation-4">
    <!-- Brand Logo -->
    <a href="index3.html" class="brand-link">
      <img src="./imagenes/LOGO11.png" alt="AdminLTE Logo" class="brand-image img-circle elevation-3" style="opacity: .8">
      <span class="brand-text font-weight-light">SISTEMA</span>
    </a>

    <!-- Sidebar -->
    <div class="sidebar">   

      <!-- Sidebar Menu -->
      <?php
        include_once("menu.php");
      ?>
      <!-- /.sidebar-menu -->
    </div>
    <!-- /.sidebar -->
  </aside>

  <!-- Content Wrapper. Contains page content -->
  <div class="content-wrapper">
    <!-- Content Header (Page header) -->
    <div class="content-header">
      <div class="container-fluid">
       
      </div><!-- /.container-fluid -->
    </div>
    <!-- /.content-header -->

    <!-- Main content -->
    <section class="content">
      <div class="container-fluid">
        <div class="row">
          <!-- Carrusel de imágenes -->
          <div class="container my-5">
            <div id="carouselExample" class="carousel slide" data-bs-ride="carousel">
              <div class="carousel-inner">
                <!-- Imagen 1 -->
                <div class="carousel-item active">
                  <img src="imagenes/1111.jpg" class="d-block w-100" alt="Imagen 1">
                </div>
                <!-- Imagen 2 -->
                <div class="carousel-item">
                  <img src="imagenes/2.jpg" class="d-block w-90" alt="Imagen 2">
                </div>
                <!-- Imagen 3 -->
                <div class="carousel-item">
                  <img src="imagenes/3.jpg" class="d-block w-100" alt="Imagen 3">
                
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>

</div>

<!-- Incluir Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.min.js"></script>

</body>
</html>

