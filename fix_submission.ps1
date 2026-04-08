# fix_submission.ps1 - Run this in your repo root
Write-Host "🔧 FIXING META HACKATHON SUBMISSION" -ForegroundColor Cyan

# 1. Delete old graders.py
if (Test-Path "graders.py") {
    Remove-Item "graders.py" -Force
    Write-Host "✅ Deleted graders.py" -ForegroundColor Green
} else {
    Write-Host "✅ graders.py already deleted" -ForegroundColor Green
}

# 2. Update all imports
Get-ChildItem -Recurse -Filter "*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match 'from graders|import graders') {
        $content = $content -replace 'from graders import', 'from safe_grader import'
        $content = $content -replace 'import graders', 'import safe_grader'
        Set-Content $_.FullName -Value $content -NoNewline
        Write-Host "✅ Updated: $($_.Name)" -ForegroundColor Green
    }
}

# 3. Fix raw returns in safe_grader.py if any
if (Test-Path "safe_grader.py") {
    $safeGrader = Get-Content "safe_grader.py" -Raw
    if ($safeGrader -match 'return 0[^\.]|return 1[^\.]') {
        $safeGrader = $safeGrader -replace 'return 0\r?\n', "return 0.01`n" -replace 'return 1\r?\n', "return 0.99`n"
        Set-Content "safe_grader.py" -Value $safeGrader -NoNewline
        Write-Host "✅ Fixed raw returns in safe_grader.py" -ForegroundColor Green
    } else {
        Write-Host "✅ No raw returns found in safe_grader.py" -ForegroundColor Green
    }
}

# 4. Final verification
Write-Host "`n=== VERIFICATION ===" -ForegroundColor Yellow
$issues = @()
if (Test-Path "graders.py") { $issues += "graders.py still exists" }
$oldImports = Select-String -Path "*.py" -Pattern "from graders|import graders" -ErrorAction SilentlyContinue
if ($oldImports) { $issues += "Old imports found" }
$rawReturns = Select-String -Path "*.py" -Pattern "return 0`$|return 1`$|return 0\.0|return 1\.0" -ErrorAction SilentlyContinue
if ($rawReturns) { $issues += "Raw returns found" }

if ($issues.Count -eq 0) {
    Write-Host "✅ ALL CHECKS PASSED - Ready to submit!" -ForegroundColor Green
} else {
    Write-Host "❌ ISSUES FOUND:" -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}
