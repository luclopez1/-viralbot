# Configura el Programador de Tareas de Windows para generar y subir 5 videos al dia
# Ejecutar como Administrador

$pythonPath = (Get-Command python).Source
$scriptPath = "C:\Users\luclo\youtube-ia-automation\generate_content.py"
$workingDir = "C:\Users\luclo\youtube-ia-automation"
$logDir = "C:\Users\luclo\youtube-ia-automation\logs"

# Crear carpeta de logs
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$hours = @(8, 12, 16, 19, 22)

foreach ($hour in $hours) {
    $taskName = "ViralBot_$($hour)h"

    # Eliminar tarea si ya existe
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    $action = New-ScheduledTaskAction `
        -Execute $pythonPath `
        -Argument "`"$scriptPath`" >> `"$logDir\viralbot_${hour}h.log`" 2>&1" `
        -WorkingDirectory $workingDir

    $trigger = New-ScheduledTaskTrigger -Daily -At "${hour}:00"

    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -RestartCount 1 `
        -RestartInterval (New-TimeSpan -Minutes 5)

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Force | Out-Null

    Write-Host "[OK] Tarea creada: $taskName - cada dia a las ${hour}:00"
}

Write-Host ""
Write-Host "====================================="
Write-Host "5 tareas programadas correctamente:"
Write-Host "  08:00 - Video 1"
Write-Host "  12:00 - Video 2"
Write-Host "  16:00 - Video 3"
Write-Host "  19:00 - Video 4"
Write-Host "  22:00 - Video 5"
Write-Host "====================================="
Write-Host "Logs en: $logDir"
