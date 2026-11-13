$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$root=Split-Path -Parent $PSScriptRoot
$source=Join-Path $root 'assets\icon.png'
if(!(Test-Path -LiteralPath $source)){throw 'assets\icon.png bulunamadi.'}
$master=[Drawing.Bitmap]::FromFile($source)
function New-IconBitmap([int]$size){
  $bmp=New-Object Drawing.Bitmap($size,$size,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g=[Drawing.Graphics]::FromImage($bmp)
  try{$g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality;$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$g.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::HighQuality;$g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality;$g.DrawImage($master,0,0,$size,$size)}finally{$g.Dispose()}
  return $bmp
}
try{
  foreach($size in @(1024,512,256)){
    $bmp=New-IconBitmap $size
    try{$name=if($size -eq 1024){'atlas-brand-hires.png'}else{"atlas-icon-$size.png"};$bmp.Save((Join-Path $root "assets\$name"),[Drawing.Imaging.ImageFormat]::Png)}finally{$bmp.Dispose()}
  }
  $frames=New-Object System.Collections.Generic.List[byte[]]
  foreach($size in @(256,128,64,48,32,24,16)){
    $bmp=New-IconBitmap $size
    try{$ms=New-Object IO.MemoryStream;$bmp.Save($ms,[Drawing.Imaging.ImageFormat]::Png);$frames.Add($ms.ToArray());$ms.Dispose()}finally{$bmp.Dispose()}
  }
  $icoPath=Join-Path $root 'assets\atlas-icon.ico';$fs=[IO.File]::Create($icoPath);$writer=New-Object IO.BinaryWriter($fs)
  try{$writer.Write([UInt16]0);$writer.Write([UInt16]1);$writer.Write([UInt16]$frames.Count);$offset=6+16*$frames.Count;for($i=0;$i -lt $frames.Count;$i++){$size=@(256,128,64,48,32,24,16)[$i];$data=$frames[$i];$writer.Write([byte]$(if($size -eq 256){0}else{$size}));$writer.Write([byte]$(if($size -eq 256){0}else{$size}));$writer.Write([byte]0);$writer.Write([byte]0);$writer.Write([UInt16]1);$writer.Write([UInt16]32);$writer.Write([UInt32]$data.Length);$writer.Write([UInt32]$offset);$offset+=$data.Length};foreach($data in $frames){$writer.Write($data)}}finally{$writer.Dispose();$fs.Dispose()}
}finally{$master.Dispose()}
Write-Host 'Windows, pencere, görev cubugu ve marka simgeleri assets\icon.png kaynagindan uretildi.' -ForegroundColor Green
