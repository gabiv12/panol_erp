param(
  [int]$Port = 8000,
  [ValidateSet("LocalSubnet","Any","Custom")][string]$Scope = "LocalSubnet",
  [string]$RemoteAddresses = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ruleName = "LaTermalERP HTTP $Port"

# Borrar reglas previas con el mismo nombre
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue

if($Scope -eq "Custom"){
  if([string]::IsNullOrWhiteSpace($RemoteAddresses)){
    throw "Scope=Custom requiere -RemoteAddresses (ej: 192.168.1.0/24)"
  }
  New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -RemoteAddress $RemoteAddresses | Out-Null
  Write-Host "Firewall: permitido puerto $Port para $RemoteAddresses"
  exit 0
}

if($Scope -eq "Any"){
  New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
  Write-Host "Firewall: permitido puerto $Port para cualquier origen (NO recomendado)"
  exit 0
}

# LocalSubnet
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -RemoteAddress LocalSubnet | Out-Null
Write-Host "Firewall: permitido puerto $Port solo para la subred local"
