<!DOCTYPE html>
<html lang="en">

<head>
  <?php
  include_once("encabezado.php");
  ?>
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
        <span class="brand-text font-weight-light">Somnolencia</span>
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
      
      <section class="content">
        <div class="container-fluid">
          <div class="row">
            <div class="col-12">

              <div class="card">
                <div class="card-header">
                  <h3 class="card-title">Viajes</h3>
                </div>
                <!-- /.card-header -->
                <div class="card-body">
                  <table id="example1" class="table table-bordered table-striped">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Fecha y Hora</th>
                        <th>Parpadeos</th>
                        <th>Cabeceos</th>
                        <th>Vostesos</th>
                        
                      </tr>
                    </thead>
                    <tbody>

                      <?php
                      include_once("bdcone.php");
                      $consulta = $cadena->prepare("SELECT * FROM viaje");
                      $consulta->execute();
                      $consultatabla = $consulta->fetchAll(PDO::FETCH_ASSOC);
                      foreach ($consultatabla as $viaje) {
                        $id_viaje  = $viaje['id_viaje'];
                        $hora_viaje = $viaje['hora_viaje'];
                        $parpadeo = $viaje['parpadeo'];
                        $cabeceos = $viaje['cabeceos'];
                        $bosteso = $viaje['bosteso'];
                        
                        ?>
                        <tr>
                          <td><?php echo $id_viaje ?></td>
                          <td><?php echo $hora_viaje ?> </td>
                          <td><?php echo $parpadeo ?></td>
                          <td><?php echo $cabeceos ?> </td>
                          <td><?php echo $bosteso ?> </td>
                        </tr>
                      <?php } ?>

                    </tbody>

                  </table>
                </div>
                <!-- /.card-body -->
              </div>
              <!-- /.card -->
            </div>
            <!-- /.col -->
          </div>
          <!-- /.row -->
        </div>
        <!-- /.container-fluid -->
      </section>

      <!-- /.content -->
    </div>

   