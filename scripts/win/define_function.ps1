function red {
  process { Write-Host $_ -ForegroundColor red }
}

function cyan {
  process { Write-Host $_ -ForegroundColor cyan }
}

function green {
  process { Write-Host $_ -ForegroundColor green }
}

function Error {
  param($Message = "Error!", $ErrorCode = 1)
  Write-Output $Message | red
  $host.SetShouldExit($ErrorCode)
  Exit
}

function ErrorInSourcedFile {
  param($Message = "Error!", $ErrorCode = 1)
  Write-Output $Message | red
  [Environment]::Exit($ErrorCode)
}

function PrintInfo {
  param($Message = "Info?")
  Write-Output $Message | cyan
}

function End_OK {
  $host.SetShouldExit(0)
  Exit
}