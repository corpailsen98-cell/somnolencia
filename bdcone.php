<?php 
    define('SERVIDOR','localhost');
    define('USUARIO','root');
    define('CLAVE','');
    define('BD','somnolencia');

    $servidor = "mysql:dbname=".BD."; host=".SERVIDOR;
    try{
        $cadena = new PDO($servidor, username:USUARIO, password:CLAVE);
        //echo "<script> alert('CAPO ERE CONEXION EXISTOSA') </script>";
    } catch(PDOException $e){
        echo "<script> alert('CHACRA! NO HAY BASE DE DATOS') </script>";

    }
    $mysql = new mysqli("localhost","root","","somnolencia");
?>