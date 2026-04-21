<?php
// Página de prueba para la API de bgremover.
// Subir al web root del subdominio: /var/www/bgremover.tutansoft.com/html/

define('API_URL', 'http://127.0.0.1:8001/api/v1/remove-bg');
define('MAX_SIZE_MB', 10);

$result   = null;
$error    = null;
$duration = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $file = $_FILES['image'] ?? null;

    if (!$file || $file['error'] !== UPLOAD_ERR_OK) {
        $error = 'No se recibió ninguna imagen.';
    } elseif ($file['size'] > MAX_SIZE_MB * 1024 * 1024) {
        $error = 'La imagen supera el límite de ' . MAX_SIZE_MB . ' MB.';
    } else {
        $threshold = max(0, min(255, (int)($_POST['threshold'] ?? 20)));

        $token = trim($_POST['token'] ?? '');

        $ch = curl_init(API_URL);
        $headers = [];
        if ($token !== '') {
            $headers[] = 'Authorization: Bearer ' . $token;
        }
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => $headers,
            CURLOPT_POSTFIELDS     => [
                'image'     => new CURLFile($file['tmp_name'], $file['type'], $file['name']),
                'threshold' => $threshold,
            ],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 120,
        ]);

        $t0       = microtime(true);
        $body     = curl_exec($ch);
        $duration = round(microtime(true) - $t0, 2);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $mime     = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
        curl_close($ch);

        if ($httpCode === 200 && str_starts_with($mime, 'image/')) {
            // Devuelve la imagen directamente como descarga.
            header('Content-Type: image/png');
            header('Content-Disposition: attachment; filename="sin_fondo.png"');
            header('X-Processing-Time: ' . $duration . 's');
            echo $body;
            exit;
        }

        // Si no es imagen, la respuesta es JSON de error.
        $detail = json_decode($body, true);
        $error  = $detail['message'] ?? $detail['error'] ?? "Error HTTP $httpCode";
    }
}
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BGRemover — prueba de API</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f0f2f5; display: flex; justify-content: center; padding: 2rem 1rem; }
  .card { background: #fff; border-radius: 12px; padding: 2rem; width: 100%; max-width: 480px; box-shadow: 0 2px 12px rgba(0,0,0,.1); }
  h1 { font-size: 1.25rem; margin-bottom: 1.5rem; color: #1a1a2e; }
  label { display: block; font-size: .85rem; font-weight: 600; color: #444; margin-bottom: .3rem; }
  input[type=file], input[type=range] { width: 100%; margin-bottom: 1rem; }
  .row { display: flex; align-items: center; gap: .75rem; margin-bottom: 1rem; }
  .row input[type=range] { flex: 1; margin: 0; }
  .row span { font-size: .9rem; width: 2rem; text-align: right; color: #333; }
  button { width: 100%; padding: .75rem; background: #4f46e5; color: #fff; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
  button:hover { background: #4338ca; }
  .error { margin-top: 1rem; padding: .75rem 1rem; background: #fee2e2; color: #b91c1c; border-radius: 8px; font-size: .9rem; }
  .info  { margin-top: 1rem; padding: .75rem 1rem; background: #ede9fe; color: #4f46e5; border-radius: 8px; font-size: .85rem; }
  footer { margin-top: 1.5rem; font-size: .75rem; color: #999; text-align: center; }
</style>
</head>
<body>
<div class="card">
  <h1>BGRemover — prueba de API</h1>

  <form method="post" enctype="multipart/form-data">
    <label for="token">API Token</label>
    <input type="password" id="token" name="token" placeholder="Dejar vacío si no hay token" style="width:100%;margin-bottom:1rem;padding:.45rem .6rem;border-radius:6px;border:1px solid #333;background:#111;color:#eee;">

    <label for="image">Imagen (JPG / PNG / WEBP, máx <?= MAX_SIZE_MB ?> MB)</label>
    <input type="file" id="image" name="image" accept="image/*" required>

    <label for="threshold">Threshold de alpha: <span id="val">20</span></label>
    <div class="row">
      <input type="range" id="threshold" name="threshold"
             min="0" max="255" value="20"
             oninput="document.getElementById('val').textContent=this.value">
      <span id="val2"></span>
    </div>

    <button type="submit">Quitar fondo y descargar</button>
  </form>

  <?php if ($error): ?>
    <div class="error"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>

  <?php if ($duration && !$error): ?>
    <div class="info">Procesado en <?= $duration ?> s</div>
  <?php endif; ?>

  <footer>
    <a href="/api/v1/health" target="_blank">health</a> ·
    <a href="/api/v1/models" target="_blank">models</a>
  </footer>
</div>

<script>
  // Sincroniza el valor visible con el slider.
  const slider = document.getElementById('threshold');
  const val    = document.getElementById('val');
  slider.addEventListener('input', () => val.textContent = slider.value);
</script>
</body>
</html>
