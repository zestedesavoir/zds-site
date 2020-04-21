. $PSScriptRoot\define_function.ps1

$scriptArgs=$args

$ErrorActionPreference = "Stop"

function _in {
  param ($find)
  foreach ($i in $scriptArgs) {
    if ($i -eq $find) {
      Return 1
    }
  }
  Return 0
}

#Force working directory in base folder of zds-site
$ZDS_SITE = Get-Location
Set-Location -Path "$ZDS_SITE"

$APP_PATH="$ZDS_SITE\zdsenv\App"

if (Test-Path "temp_download") {
  rm -r temp_download
}

# Install packages
if (-not (_in "-packages") -and ((_in "+packages") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Installing packages"

  $gettext_url="https://github.com/mlocati/gettext-iconv-windows/releases/download/v0.20.1-v1.16/gettext0.20.1-iconv1.16-shared-32.exe"
  $zlib_url="https://sourceforge.net/projects/gnuwin32/files/zlib/1.2.3/zlib-1.2.3.exe/download"

  mkdir temp_download | Out-Null

  PrintInfo " | -> Downloading getText..."
  (new-object System.Net.WebClient).DownloadFile($gettext_url, "temp_download\gettext.exe")
  PrintInfo " | -> Downloading zlib_url..."
  (new-object System.Net.WebClient).DownloadFile($zlib_url, "temp_download\zlib.exe")

  PrintInfo " | -> Launch getText installer..."
  Start-Process .\temp_download\gettext.exe -Wait; $exVal=$LASTEXITCODE + 0
  PrintInfo " | -> Launch zlib_url installer..."
  Start-Process .\temp_download\zlib.exe -Wait; $exVal=($LASTEXITCODE + $exVal)

  if ($exVal -ne 0) {
    Error "Error: Cannot install packages." 11
  }

  rm -r temp_download
}


# virtualenv
if (-not (_in "-virtualenv") -and ((_in "+virtualenv") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Create virtual environment"

  PrintInfo " | -> Install virtualenv."
  pip install virtualenv; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot install virtualenv with pip."
  }

  PrintInfo " | -> Create virtualenv."
  python -m virtualenv zdsenv; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot create virtualenv."
  }

  PrintInfo " | -> Create .\zdsenv\App folder for nodejs, yarn and other apps."

  if (-not (Test-Path "$APP_PATH")) {
    mkdir "$APP_PATH" | Out-Null
  }
}

PrintInfo "* Load virtualenv."

if (-not (Test-Path "$ZDS_SITE\zdsenv")) {
  Error "Error: You have to create the virtual environment zdsenv (+virtualenv) before continue."
}

. "$ZDS_SITE\zdsenv\Scripts\activate.ps1"
if ($env:virtual_env -ne "$ZDS_SITE\zdsenv") {
  Error "Error: Cannot load virtualenv."
} else {
  PrintInfo " | -> Virtualenv loaded: $VIRTUAL_ENV"
}


# node
if (-not (_in "-node") -and ((_in "+node") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Install node v10.18.0"

  mkdir temp_download | Out-Null

  $node_filename = "node-v10.18.0-win-x64"
  $node_url="https://nodejs.org/dist/v10.18.0/$node_filename.zip"

  PrintInfo " | -> Downloading NodeJS..."
  (new-object System.Net.WebClient).DownloadFile($node_url, "temp_download/node.zip")

  if (Test-Path "$APP_PATH\node") {
    PrintInfo " | -> RM old folder"
    rm -r "$APP_PATH\node"
  }
  if (Test-Path "$APP_PATH\$node_filename") {
    PrintInfo " | -> RM old cache folder"
    rm -r "$APP_PATH\$node_filename"
  }

  PrintInfo " | -> Unzip node."
  
  # unzip
  Expand-Archive "temp_download\node.zip" -DestinationPath "$APP_PATH"; $exVal=$LASTEXITCODE + 0
  ren "$APP_PATH\$node_filename" "node"; $exVal=($LASTEXITCODE + $exVal)
  if ($exVal -ne 0) {
    rm -r "$APP_PATH\$node_filename"
    Error "Error: Cannot install nodejs." 11
  }

  if (!((Get-Content zdsenv\Scripts\activate.ps1) -match "node")) {
    PrintInfo " | -> Add node in %PATH% of virtualenv."
    $text = "set `"PATH=%VIRTUAL_ENV%\App\node;%PATH%`""
    Add-Content zdsenv\Scripts\activate.bat $text
    $text = "PATH=%VIRTUAL_ENV%\App\node;%PATH%"
    Add-Content zdsenv\Scripts\activate $text
    $text = "`$env:PATH = `"`$env:VIRTUAL_ENV\App\node;`" + `$env:PATH"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "`$PATH.add(`$VIRTUAL_ENV + _get_sep() + `"App`" + _get_sep() + `"node`", front=True, replace=True)"
    Add-Content zdsenv\Scripts\activate.xsh $text
  } 

  PrintInfo "* Install yarn"
  PrintInfo " | -> Downloading yarn..."

  $yarn_url="https://legacy.yarnpkg.com/latest.msi"
  (new-object System.Net.WebClient).DownloadFile($yarn_url, "temp_download\yarn.msi")
  if (Test-Path "$APP_PATH\yarn") {
    PrintInfo " | -> RM old folder"
    rm -r "$APP_PATH\yarn"
  }

  PrintInfo " | -> Launch yarn installer..."

  Start-Process msiexec -ArgumentList "/a `"$ZDS_SITE\temp_download\yarn.msi`" /passive TARGETDIR=`"$ZDS_SITE\zdsenv\App\`"" -Wait; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot install yarn." 11
  }

  function global:yarn {
    node $ZDS_SITE\zdsenv\App\yarn\bin\yarn.js $args
  }

  if (!((Get-Content zdsenv\Scripts\activate.ps1) -match "yarn")) {
    PrintInfo " | -> Add yarn in %PATH% of virtualenv."
    $text = "set `"PATH=%VIRTUAL_ENV%\App\yarn\bin;%PATH%`""
    Add-Content zdsenv\Scripts\activate.bat $text
    $text = "PATH=%VIRTUAL_ENV%\App\yarn\bin;%PATH%"
    Add-Content zdsenv\Scripts\activate $text
    $text = "`$env:PATH = `"`$env:VIRTUAL_ENV\App\yarn\bin;`" + `$env:PATH"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "`$PATH.add(`$VIRTUAL_ENV + _get_sep() + `"App`" + _get_sep() + `"yarn`" + _get_sep() + `"bin`", front=True, replace=True)"
    Add-Content zdsenv\Scripts\activate.xsh $text
  }

  rm -r temp_download
}


# back
if (-not (_in "-back") -and ((_in "+back") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Install back dependencies and migrate"

  pip install --upgrade -r requirements-dev.txt; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot install dependencies." 11
  }

  python manage.py migrate; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot migrate database after the back installation." 11
  }
}


# front
if (-not (_in "-front") -and ((_in "+front") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Install front dependencies and build front"

  # TODO: Force parameter `rm -r node_modules`

  PrintInfo " | -> Installing front dependencies..."
  yarn install; $exVal=$LASTEXITCODE

  if ($exVal -ne 0) {
    Error "Error: Cannot install-front." 11
  }

  if (!((Get-Content zdsenv\Scripts\activate.ps1) -match "gulp")) {
    PrintInfo " | -> Add gulp alias in virtualenv."
    $text = "doskey gulp=node `"%VIRTUAL_ENV%\..\node_modules\gulp\bin\gulp.js`" $*"
    Add-Content zdsenv\Scripts\activate.bat $text
    $text = "gulp () {`r`n    node `"%VIRTUAL_ENV%\..\node_modules\gulp\bin\gulp.js`" `"$@`"`r`n}"
    Add-Content zdsenv\Scripts\activate $text
    $text = "function global:gulp {`r`n    node `"`$env:VIRTUAL_ENV\..\node_modules\gulp\bin\gulp.js`" `$args`r`n}"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "aliases[`"gulp`"] = [`"node`", `$VIRTUAL_ENV + _get_sep() + `"..`" + _get_sep() + `"node_modules`" + _get_sep() + `"gulp`" + _get_sep() + `"bin`" + _get_sep() + `"gulp.js`"]"
    Add-Content zdsenv\Scripts\activate.xsh $text
  }

  PrintInfo " | -> Building..."
  npm run build; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot build-front." 11
  }
}


# zmd
if (-not (_in "-zmd") -and ((_in "+zmd") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Install zmarkdown dependencies"

  # TODO: Add force parameter to `rm -r node_modules`

  PrintInfo " | -> Installing zmd & dependencies..."

  Set-Location -Path "$ZDS_SITE\zmd"
  npm install --production; $exVal=$LASTEXITCODE
  Set-Location -Path "$ZDS_SITE"

  if ($exVal -ne 0) {
    Error "Error: Cannot install zmd." 11
  }

  PrintInfo " | -> Configuring pm2..."

  function global:pm2 {
    node .\zmd\node_modules\pm2\bin\pm2 $args
  }

  if (!((Get-Content zdsenv\Scripts\activate.ps1) -match "pm2")) {
    PrintInfo " | -> Add pm2 alias in virtualenv."
    $text = "doskey pm2=node `"%VIRTUAL_ENV%\..\zmd\node_modules\pm2\bin\pm2`" $*"
    Add-Content zdsenv\Scripts\activate.bat $text
    $text = "pm2 () {`r`n    node `"%VIRTUAL_ENV%\..\zmd\node_modules\pm2\bin\pm2`" `"$@`"`r`n}"
    Add-Content zdsenv\Scripts\activate $text
    $text = "function global:pm2 {`r`n    node `"`$env:VIRTUAL_ENV\..\zmd\node_modules\pm2\bin\pm2`" `$args`r`n}"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "aliases[`"pm2`"] = [`"node`", `$VIRTUAL_ENV + _get_sep() + `"..`" + _get_sep() + `"zmd`" + _get_sep() + `"node_modules`" + _get_sep() + `"pm2`" + _get_sep() + `"bin`" + _get_sep() + `"pm2`"]"
    Add-Content zdsenv\Scripts\activate.xsh $text
  }
}

# fixtures
if (-not (_in "-data") -and ((_in "+data") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Generate fixtures"

  # TODO: Force parameter `rm -r node_modules`

  PrintInfo " | -> Start zmd."
  pm2 start --name=zmarkdown -f zmd\node_modules\zmarkdown\server\index.js -i 1; $exVal=$LASTEXITCODE

  if ($exVal -ne 0) {
    Error "Error: Cannot start zmd to generate-fixtures." 11
  }
  
  # prevent error, wait zmd
  # TODO add curl to check if zmd is ready
  Start-Sleep -s 5

  PrintInfo " | -> Make fixtures."
  PrintInfo " | Step 1:"
  python manage.py loaddata (dir .\fixtures\*.yaml); $exVal=$LASTEXITCODE
  PrintInfo " | Step 2:"
  python manage.py load_factory_data .\fixtures\advanced\aide_tuto_media.yaml; $exVal=($exVal + $LASTEXITCODE)
  PrintInfo " | Step 3:"
  python manage.py load_fixtures --size=low --all; $exVal=($exVal + $LASTEXITCODE)

  if ($exVal -ne 0) {
    Write-Output "Error: Error during fixtures generation." | red
  }

  PrintInfo " | -> Stop zmd."
  pm2 kill; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Write-Output "Warning: Cannot stop zmd." | red
  }
}

PrintInfo "Done. "

Write-Output "You can now run instance, start powershell console and run :" | green
Write-Output "1) Load virtualenv: '. .\zdsenv\Scripts\activate.ps1'" | green
Write-Output "2) Start zmd: 'pm2 start --name=zmarkdown -f zmd\node_modules\zmarkdown\server\index.js -i 1'" | green
Write-Output "3) Start django: 'python manage.py runserver'" | green
