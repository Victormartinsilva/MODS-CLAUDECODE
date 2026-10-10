# Instala os mods deste repositorio no Claude Code (Windows).
# Uso:  powershell -ExecutionPolicy Bypass -File .\instalar.ps1
$ErrorActionPreference = 'Stop'
$Marketplace = 'Victormartinsilva/MODS-CLAUDECODE'
$MarketName  = 'mods-victor'
$Plugins     = 'mod-store', 'flightdeck', 'skins', 'pokemon'
$Min         = [version]'2.1.287'

function Get-ClaudeVersion($exe) {
  try { $v = & $exe --version 2>$null; if ("$v" -match '(\d+\.\d+\.\d+)') { return [version]$Matches[1] } } catch {}
  return [version]'0.0.0'
}

# 1. Acha um Claude Code com suporte a mods (2.1.287+). O do PATH pode ser antigo;
#    o app desktop traz o seu proprio claude.exe em %APPDATA%\Claude\claude-code.
$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude -or (Get-ClaudeVersion $claude) -lt $Min) {
  $app = Get-ChildItem "$env:APPDATA\Claude\claude-code\*\*\claude.exe" -ErrorAction SilentlyContinue |
    Sort-Object { Get-ClaudeVersion $_.FullName } -Descending | Select-Object -First 1
  if ($app -and (Get-ClaudeVersion $app.FullName) -ge $Min) { $claude = $app.FullName }
  else { Write-Host "Precisa do Claude Code $Min ou superior. Rode 'claude update' e tente de novo." -ForegroundColor Red; exit 1 }
}
Write-Host "Usando $claude ($(Get-ClaudeVersion $claude))" -ForegroundColor Cyan

# 2. Adiciona este marketplace.
& $claude plugin marketplace add $Marketplace

# 3. Instala cada mod. Se ja estiver instalado (de qualquer marketplace), mantem o existente
#    para nao carregar duas copias.
$list = (& $claude plugin list 2>&1) -join "`n"
$ids = @{}
foreach ($p in $Plugins) {
  if ($list -match "\s($([regex]::Escape($p))@[\w.-]+)") {
    $ids[$p] = $Matches[1]; Write-Host "$p ja instalado como $($Matches[1])"
  } else {
    $ids[$p] = "$p@$MarketName"; & $claude plugin install $ids[$p]
  }
}

# 4. Ajustes: rotulos do flightdeck em portugues.
$gate = "PERMISS$([char]0x00D5)ES"
& $claude plugin install $ids['flightdeck'] --config architectLabel=ARQUITETO --config "gateLabel=$gate"

Write-Host ""
Write-Host "Pronto. No Claude Code, rode:" -ForegroundColor Green
Write-Host "  /reload-plugins"
Write-Host "  /skin dracula"
Write-Host "  /skin band off"
Write-Host "  /pokemon abra"
