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

  PrintInfo " | -> Installation will ask permission for PowerShell."
  Start-Process powershell -Verb RunAs -ArgumentList "Set-ExecutionPolicy RemoteSigned" -WindowStyle Hidden -Wait
  $OutputVariable = Get-ExecutionPolicy
  if ($OutputVariable -ne "RemoteSigned") {
    Error "Error: Cannot change ExecutionPolicy property to 'RemoteSigned'." 11
  }

  PrintInfo " | -> Install virtualenv."
  pip install virtualenv; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot install virtualenv with pip."
  }

  PrintInfo " | -> Create virtualenv."
  virtualenv zdsenv; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot create virtualenv."
  }
}

PrintInfo "* Load virtualenv."

if (-not (Test-Path "$ZDS_SITE\zdsenv")) {
  Error "Error: You have to create the virtual environment zdsenv (+virtualenv) before continue."
}

. "$ZDS_SITE\zdsenv\Scripts\activate.ps1"
if ($env:virtual_env -ne "$ZDS_SITE\zdsenv") {
  Error "Error: Cannot load virtualenv."
}


# node
if (-not (_in "-node") -and ((_in "+node") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Install node v10.8.0"

  mkdir temp_download | Out-Null

  $node_url="https://nodejs.org/dist/v10.8.0/node-v10.8.0-win-x64.zip"

  PrintInfo " | -> Downloading NodeJS..."
  (new-object System.Net.WebClient).DownloadFile($node_url, "temp_download/node.zip")


  PrintInfo " | -> Init .\zdsenv\App for nodejs."

  $node_path="$ZDS_SITE\zdsenv\App"
  if (-not (Test-Path "$node_path")) {
    mkdir "$node_path" | Out-Null
  }
  if (Test-Path "$node_path\node") {
    PrintInfo " | -> RM old folder"
    rm -r "$node_path\node"
  }

  PrintInfo " | -> Unzip node."
  
  unzip -q temp_download\node.zip -d "$node_path"; $exVal=$LASTEXITCODE + 0
  ren "$node_path\node-v10.8.0-win-x64" node; $exVal=($LASTEXITCODE + $exVal)
  if ($exVal -ne 0) {
    Error "Error: Cannot install nodejs." 11
  }

  if (!((Get-Content zdsenv\Scripts\activate.bat) -match "node")) {
    PrintInfo " | -> Add node in %PATH% of virtualenv."
    $text = "set `"PATH=%VIRTUAL_ENV%\App\node;%PATH%`""
    Add-Content zdsenv\Scripts\activate.bat $text
    $text = "PATH=%VIRTUAL_ENV%\App\node;%PATH%"
    Add-Content zdsenv\Scripts\activate $text
    $text = "`$env:PATH = `"`$env:VIRTUAL_ENV/App/node;`" + `$env:PATH"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "`$PATH.add(`$VIRTUAL_ENV + _get_sep() + `"App`" + _get_sep() + `"node`", front=True, replace=True)"
    Add-Content zdsenv\Scripts\activate.xsh $text
  } 

  rm -r temp_download

  PrintInfo "* Install yarn"

  npm install yarn --no-save

  if (!((Get-Content zdsenv\Scripts\activate.bat) -match "yarn")) {
    PrintInfo " | -> Add yarn alias in virtualenv."
    $text = "yarn () {`r`n    node ./node_modules/yarn/bin/yarn.js `"$@`"`r`n}"
    Add-Content zdsenv\Scripts\activate $text
    $text = "function global:yarn {`r`n    node ./node_modules/yarn/bin/yarn.js $args`r`n}"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "aliases[`"yarn`"] = [`"node`", `"./node_modules/yarn/bin/yarn.js`"]"
    Add-Content zdsenv\Scripts\activate.xsh $text
  }
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
  node ./node_modules/yarn/bin/yarn.js install; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Error "Error: Cannot install-front." 11
  }

  if (!((Get-Content zdsenv\Scripts\activate.bat) -match "gulp")) {
    PrintInfo " | -> Add gulp alias in virtualenv."
    $text = "gulp () {`r`n    node ./node_modules/gulp/bin/gulp.js `"$@`"`r`n}"
    Add-Content zdsenv\Scripts\activate $text
    $text = "function global:gulp {`r`n    node ./node_modules/gulp/bin/gulp.js $args`r`n}"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "aliases[`"gulp`"] = [`"node`", `"./node_modules/gulp/bin/gulp.js`"]"
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

  PrintInfo " | -> Installing pm2..."
  npm install pm2 --no-save

  if (!((Get-Content zdsenv\Scripts\activate.bat) -match "pm2")) {
    PrintInfo " | -> Add pm2 alias in virtualenv."
    $text = "pm2 () {`r`n    node ./node_modules/pm2/bin/pm2 `"$@`"`r`n}"
    Add-Content zdsenv\Scripts\activate $text
    $text = "function global:pm2 {`r`n    node ./node_modules/pm2/bin/pm2 $args`r`n}"
    Add-Content zdsenv\Scripts\activate.ps1 $text
    $text = "aliases[`"pm2`"] = [`"node`", `"./node_modules/pm2/bin/pm2`"]"
    Add-Content zdsenv\Scripts\activate.xsh $text
  }

  Set-Location -Path "$ZDS_SITE\zmd"

  PrintInfo " | -> Installing zmd & dependencies..."
  npm install --production; $exVal=($exVal + $LASTEXITCODE)

  if ($exVal -ne 0) {
    Error "Error: Cannot install zmd." 11
  }

  Set-Location -Path "$ZDS_SITE"
}


# fixtures
if (-not (_in "-data") -and ((_in "+data") -or (_in "+base") -or (_in "+full"))) {
  PrintInfo "* Generate fixtures"

  # TODO: Force parameter `rm -r node_modules`

  PrintInfo " | -> Start zmd."
  node ./node_modules/pm2/bin/pm2 start --name=zmarkdown -f zmd/node_modules/zmarkdown/server/index.js -i 1; $exVal=$LASTEXITCODE

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
  node ./node_modules/pm2/bin/pm2 kill; $exVal=$LASTEXITCODE
  if ($exVal -ne 0) {
    Write-Output "Warning: Cannot stop zmd." | red
  }
}

PrintInfo "Done. "

Write-Output "You can now run instance, start powershell console and run :" | green
Write-Output "1) Load virtualenv: '. .\zdsenv\Scripts\activate.ps1'" | green
Write-Output "2) Start zmd: 'pm2 start --name=zmarkdown -f zmd/node_modules/zmarkdown/server/index.js -i 1'" | green
Write-Output "3) Start django: 'python manage.py runserver'" | green
