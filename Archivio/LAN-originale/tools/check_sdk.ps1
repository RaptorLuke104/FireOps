param([Parameter(Mandatory=$true)][string]$Sdk)
$ErrorActionPreference='Stop'
Write-Host '=== SimConnect native x64 DLL ==='
Get-ChildItem $Sdk -Recurse -Filter SimConnect.dll | Select-Object FullName
Write-Host '=== Header che dichiara fsVfxSpawnInWorld ==='
Get-ChildItem "$Sdk\WASM" -Recurse -Filter *.h | Select-String -Pattern 'fsVfxSpawnInWorld' | Select-Object Path,LineNumber,Line
Write-Host '=== Progetti di riferimento ==='
Get-ChildItem $Sdk -Recurse -Filter *.xml | Where-Object { $_.Name -match 'SimpleFX|StandaloneModule' } | Select-Object FullName
Write-Host 'Usare il toolset/template SDK 2024; non usare emcc o il template MSFS 2020.'
