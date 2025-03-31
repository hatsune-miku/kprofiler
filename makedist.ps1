function Remove-Pycache() {
    Remove-Item */__pycache__ -Force -Recurse -ErrorAction Ignore
}

function Invoke-EnsureEmptyPath($Path, $Clear = $true) {
    if ($Clear) {
        Remove-Item $Path -Force -Recurse -ErrorAction Ignore
    }
    New-Item -ItemType Directory -Force -Path $Path     
}

Remove-Pycache

Invoke-EnsureEmptyPath dist
Invoke-EnsureEmptyPath out -Clear $false

Copy-Item -Recurse core dist
Copy-Item -Recurse doc dist
Copy-Item -Recurse helpers dist
Copy-Item -Recurse server dist
Copy-Item -Recurse tss dist
Copy-Item -Recurse utils dist

Copy-Item -Recurse frontend/dist dist/frontend/dist

Copy-Item config.yaml dist
Copy-Item main.py dist
Copy-Item README.md dist
Copy-Item requirements.txt dist
Copy-Item kp-start.ps1 dist

$Date = Get-Date -Format "MMdd-HHmm"

Compress-Archive dist/* "out/kprofiler-$($Date).zip" -Force
