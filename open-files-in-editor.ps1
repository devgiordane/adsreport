# open-files-in-editor.ps1

$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Abre só a pasta do projeto
code $projectPath

Start-Sleep -Seconds 2

# Arquivos .py, ignorando pastas de ambiente e cache
$pythonFiles = Get-ChildItem -Path $projectPath -Recurse -File -Filter *.py |
    Where-Object {
        $_.FullName -notmatch '\\(\.env|\.venv|venv|env|\.git|node_modules)(\\|$)'
    } |
    Select-Object -ExpandProperty FullName

if (-not $pythonFiles -or $pythonFiles.Count -eq 0) {
    Write-Host "Nenhum arquivo .py encontrado."
    exit
}

$batchSize = 3000

for ($i = 0; $i -lt $pythonFiles.Count; $i += $batchSize) {
    $end = [Math]::Min($i + $batchSize - 1, $pythonFiles.Count - 1)
    $batch = $pythonFiles[$i..$end]
    code --reuse-window @batch
}

Write-Host "$($pythonFiles.Count) arquivos Python abertos."