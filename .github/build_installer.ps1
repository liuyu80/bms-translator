Write-Host "开始构建安装程序..." -ForegroundColor Green

try {
    Write-Host "正在检查 Python 版本..."
    $pythonVersion = (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if (-not $pythonVersion) {
        throw "无法获取 Python 版本，请确保 Python 已安装并配置在 PATH 中。"
    }
    Write-Host "检测到 Python 版本: $pythonVersion" -ForegroundColor Cyan

    # 假设需要 Python 3.x
    if ($pythonVersion.StartsWith("2.")) {
        throw "检测到 Python 2.x 版本，请使用 Python 3.x 版本。"
    }
    Write-Host "Python 版本检查通过。" -ForegroundColor Green

    Write-Host "正在执行 PyInstaller..."
    python -m PyInstaller ui.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller 执行失败，退出代码: $LASTEXITCODE"
    }
    Write-Host "PyInstaller 执行成功。" -ForegroundColor Green

    Write-Host "正在获取最新的 Git 标签..."
    $latestTag = git describe --tags --abbrev=0
    if (-not $latestTag) {
        throw "无法获取最新的 Git 标签。"
    }
    $bmsPathName = "bms-translator-" + $latestTag
    Write-Host "最新标签: $latestTag" -ForegroundColor Cyan
    Write-Host "构建路径名称: $bmsPathName" -ForegroundColor Cyan

    Write-Host "正在创建目标目录: $bmsPathName"
    mkdir -p $bmsPathName
    if (-not (Test-Path $bmsPathName)) {
        throw "无法创建目录: $bmsPathName"
    }
    Write-Host "目标目录创建成功。" -ForegroundColor Green

    Write-Host "正在复制 config/ 目录..."
    cp -r config/ $bmsPathName/config/
    if ($LASTEXITCODE -ne 0) {
        throw "复制 config/ 目录失败。"
    }
    Write-Host "config/ 目录复制成功。" -ForegroundColor Green

    Write-Host "正在复制 dist/ui.exe..."
    cp dist/ui.exe $bmsPathName/$bmsPathName.exe
    if ($LASTEXITCODE -ne 0) {
        throw "复制 dist/ui.exe 失败。"
    }
    Write-Host "dist/ui.exe 复制成功。" -ForegroundColor Green

    Write-Host "构建目录结构:"
    tree $bmsPathName

    Write-Host "正在压缩文件到: $bmsPathName.zip"
    Compress-Archive -Path "$bmsPathName" -DestinationPath "$bmsPathName.zip" -Force
    if (-not (Test-Path "$bmsPathName.zip")) {
        throw "压缩文件失败。"
    }
    Write-Host "文件压缩成功: $bmsPathName.zip" -ForegroundColor Green

    Write-Host "安装程序构建完成！" -ForegroundColor Green
    echo "installer_zip_path=$bmsPathName.zip" >> $env:GITHUB_OUTPUT
}
catch {
    Write-Error "构建安装程序时发生错误: $($_.Exception.Message)"
    exit 1
}