# Excel本体で xlsx を裏で開き、Excel が実際に認識している行の高さ・列幅・文字設定を読み取る。
# 使い方: python .claude/scripts/run_powershell.py -f tests\excel_measure.ps1 -- <xlsxのフルパス>
#   （引数なしなら tests\output の plain_*.xlsx の最新を使う）。結果は tests\output\excel_measure_result.txt
# 由来: 2026-09-18 ExcelJS 出力に表示設定（sheetViews）が無いと Excel が行高を 0.8倍で解釈する現象の実測用。
param([string]$Target = "")
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$outDir = Join-Path $here "output"
$outFile = Join-Path $outDir "excel_measure_result.txt"
if (Test-Path $outFile) { Remove-Item $outFile }
if ($Target -eq "") {
  $Target = (Get-ChildItem (Join-Path $outDir "plain_*.xlsx") | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($Target, 0, $true)
  $ws = $wb.Worksheets.Item(1)
  Add-Content -Encoding UTF8 -Path $outFile -Value ("file: " + $Target)
  $hs = @(1,2,3,4,23,24,25,26) | ForEach-Object { [math]::Round($ws.Rows.Item($_).RowHeight, 2) }
  Add-Content -Encoding UTF8 -Path $outFile -Value ("行高(Excel認識) 1,2,3,4,23,24,25,26: " + ($hs -join ", "))
  $cw = @(1,2,3,4,5,6,7,8) | ForEach-Object { [math]::Round($ws.Columns.Item($_).ColumnWidth, 2) }
  Add-Content -Encoding UTF8 -Path $outFile -Value ("列幅 A-H: " + ($cw -join ", "))
  foreach ($a in @("A1","A2","H2","A3","H3","A25","A26")) {
    $c = $ws.Range($a)
    Add-Content -Encoding UTF8 -Path $outFile -Value ("{0}: {1} {2}pt bold={3} shrink={4} wrap={5} fmt={6}" -f $a, $c.Font.Name, $c.Font.Size, $c.Font.Bold, $c.ShrinkToFit, $c.WrapText, $c.NumberFormat)
  }
  Add-Content -Encoding UTF8 -Path $outFile -Value ("zoom: " + $xl.ActiveWindow.Zoom)
  $wb.Close($false)
} finally {
  $xl.Quit()
  [System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null
}
