<?php
  include_once("bdcone.php");
?>
<!DOCTYPE html>
<html lang="en">
<head>
    
<meta charset="utf-8">
    
    <link rel="stylesheet" href="estilos/stylen.css">
    
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SIS VENTAS</title>

  <link rel="stylesheet" href="estilos/adminlte.min.css">
</head>
<body class="hold-transition login-page">
<div class="login-box">
  <!-- /.login-logo -->
  <div class="card card-outline card-primary">
    <div class="card-header text-center">
      <img src="./imagenes/LOGO11.png" height="80" width="60" alt="AdminLTE Logo" class="brand-image img-circle elevation-3" style="opacity: .8">
    </div>
    <div class="card-body">
      <p class="login-box-msg">REGISTRESE</p>

      <form action="logincone.php" method="post">
        <label for="">USUARIO</label>
        <div class="input-group mb-3">
          <input type="text" class="form-control" placeholder="Ingrese su Usuario" name="txtusuario" >
          <div class="input-group-append">
            <div class="input-group-text">
              <span class="fas fa-user"></span>
            </div>
          </div>
        </div>
        <label for="">CONTRASEÑA</label>
        <div class="input-group mb-3">
          <input type="password" class="form-control" placeholder="Ingrese su contraseña" name="txtclave" >
          <div class="input-group-append">
            <div class="input-group-text">
              <span class="fas fa-lock"></span>
            </div>
          </div>
        </div>
        <div class="row">
          
          <!-- /.col -->
          <div class="col-12">
            <button type="submit" class="btn btn-primary btn-block">INGRESAR</button>
          </div>
          <!-- /.col -->
        </div>
      </form>

    </div>
    <!-- /.card-body -->
  </div>
  <!-- /.card -->
</div>
</body>
</html>
