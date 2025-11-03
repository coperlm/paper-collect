# 快速启动脚本
# 适用于Windows PowerShell

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  论文收集工具 - 快速启动" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
Write-Host "检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python已安装: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到Python，请先安装Python 3.7+" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host ""
Write-Host "检查依赖包..." -ForegroundColor Yellow
$pipList = pip list 2>&1
$requiredPackages = @("requests", "beautifulsoup4", "lxml", "pyyaml", "tqdm")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    if ($pipList -match $package) {
        Write-Host "✓ $package 已安装" -ForegroundColor Green
    } else {
        Write-Host "✗ $package 未安装" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "发现缺失的依赖包，是否现在安装？(y/n)" -ForegroundColor Yellow
    $install = Read-Host
    if ($install -eq "y" -or $install -eq "Y") {
        Write-Host "安装依赖包..." -ForegroundColor Yellow
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 依赖安装失败" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ 依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "请手动运行: pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "选择操作：" -ForegroundColor Cyan
Write-Host "1. 收集所有会议的论文元数据" -ForegroundColor White
Write-Host "2. 收集三大密码学会议 (2020-2024)" -ForegroundColor White
Write-Host "3. 收集Big4安全会议 (2020-2024)" -ForegroundColor White
Write-Host "4. 收集2024年的所有论文" -ForegroundColor White
Write-Host "5. 下载所有待下载的PDF" -ForegroundColor White
Write-Host "6. 查看统计信息" -ForegroundColor White
Write-Host "7. 执行完整流程（收集+下载）" -ForegroundColor White
Write-Host "8. 重试失败的下载" -ForegroundColor White
Write-Host "9. 自定义命令" -ForegroundColor White
Write-Host "0. 退出" -ForegroundColor White
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "请输入选项 (0-9)"

switch ($choice) {
    "1" {
        Write-Host "收集所有会议的论文元数据..." -ForegroundColor Yellow
        python main.py collect
    }
    "2" {
        Write-Host "收集三大密码学会议..." -ForegroundColor Yellow
        python main.py collect --conferences crypto asiacrypt eurocrypt --years 2020 2021 2022 2023 2024
    }
    "3" {
        Write-Host "收集Big4安全会议..." -ForegroundColor Yellow
        python main.py collect --conferences usenix_security sp ccs ndss --years 2020 2021 2022 2023 2024
    }
    "4" {
        Write-Host "收集2024年的所有论文..." -ForegroundColor Yellow
        python main.py collect --years 2024
    }
    "5" {
        Write-Host "下载所有待下载的PDF..." -ForegroundColor Yellow
        python main.py download
    }
    "6" {
        Write-Host "查看统计信息..." -ForegroundColor Yellow
        python main.py stats
    }
    "7" {
        Write-Host "执行完整流程..." -ForegroundColor Yellow
        python main.py all
    }
    "8" {
        Write-Host "重试失败的下载..." -ForegroundColor Yellow
        python main.py retry
    }
    "9" {
        Write-Host "请输入自定义命令（不含'python main.py'）：" -ForegroundColor Yellow
        $customCmd = Read-Host
        python main.py $customCmd
    }
    "0" {
        Write-Host "再见！" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host "无效选项" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "操作完成！" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
