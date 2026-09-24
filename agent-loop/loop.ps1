<#
Agent loop entry point (Windows PowerShell 5.1+ / PowerShell 7). ASCII-only file.

  .\loop.ps1                      run the loop (poll tasks/inbox, process tasks)
  .\loop.ps1 once                 process at most one task, then exit
  .\loop.ps1 report               regenerate agent-loop/a1/data.js
  .\loop.ps1 selftest             check git, claude CLI, flags and the real model id (1 short call)
  .\loop.ps1 new -Title .. -Goal .. -DoneWhen .. -Scope zadani/x.md [-Mode spec|code] [-Inputs a,b] [-MaxRounds 5] [-MaxMinutes 60] [-Notes ..]
  .\loop.ps1 restart -Id TASK-0003 [-FromScratch]
  .\loop.ps1 stop                 create STOP (loop ends before the next round)
  .\loop.ps1 resume               remove STOP
#>
param(
    [Parameter(Position = 0)][ValidateSet('run', 'once', 'report', 'selftest', 'new', 'restart', 'stop', 'resume')][string]$Command = 'run',
    [string]$Title, [string]$Goal, [string]$DoneWhen, [string[]]$Scope, [ValidateSet('spec', 'code')][string]$Mode = 'spec',
    [string[]]$Inputs = @(), [string[]]$Deny = @(), [int]$MaxRounds = 0, [int]$MaxMinutes = 0, [int]$Priority = 100, [string]$Notes = '',
    [string]$Id, [switch]$FromScratch
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'lib/AgentLoop.ps1')

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Initialize-Loop $repo

switch ($Command) {
    'run'     { Start-Loop }
    'once'    { Start-Loop -Once }
    'report'  { Update-Report; Write-Log 'agent-loop/a1/data.js updated' }
    'new'     { New-LoopTask -Title $Title -Goal $Goal -DoneWhen $DoneWhen -ScopeAllow $Scope -Mode $Mode -Inputs $Inputs -ScopeDeny $Deny -MaxRounds $MaxRounds -MaxMinutes $MaxMinutes -Priority $Priority -Notes $Notes | Out-Null }
    'restart' { Restart-LoopTask -Id $Id -FromScratch:$FromScratch }
    'stop'    { Write-Text (Get-RepoPath 'STOP') ((Get-Now) + "`n"); Write-Log 'STOP created' }
    'resume'  { Remove-Item -LiteralPath (Get-RepoPath 'STOP') -Force -ErrorAction SilentlyContinue; Write-Log 'STOP removed' }
    'selftest' {
        Write-Log ('repo: ' + $repo + ' | branch: ' + (Get-GitBranch) + ' | remote: ' + (Test-Remote) + ' | clean: ' + (Test-TreeClean))
        Resolve-Claude | Out-Null
        $caps = Get-ClaudeCaps
        Write-Log ('claude: ' + $caps.path + ' | ' + $caps.version + ' | --effort: ' + $caps.effort + ' | --bare: ' + $caps.bare)
        $a = @('-p', '--model', [string](Get-Cfg 'model'), '--output-format', 'json')
        if ($caps.effort) { $a += @('--effort', [string](Get-Cfg 'effort')) }
        $r = Invoke-Native -File $script:Claude -Arguments $a -StdIn 'Reply with the single word OK.' -TimeoutSec 600 -Env @{ 'CLAUDE_CODE_EFFORT_LEVEL' = [string](Get-Cfg 'effort') }
        $j = ConvertFrom-ClaudeOutput $r.Out
        $mu = Get-Prop $j 'modelUsage' $null
        $models = @(); if ($mu) { $models = @($mu.PSObject.Properties | ForEach-Object { $_.Name }) }
        Write-Log ('exit: ' + $r.Code + ' | result: ' + [string](Get-Prop $j 'result' '') + ' | models: ' + ($models -join ', ') + ' | cost_usd: ' + (Get-Prop $j 'total_cost_usd' 'n/a'))
        if ($r.Code -ne 0) { Write-Log ('stderr: ' + $r.Err.Trim()); Write-Log ('stdout: ' + (Limit-Text $r.Out 2)) }
        $exp = [string](Get-Cfg 'model_expect')
        if ($models.Count -gt 0 -and -not (@($models | Where-Object { $_ -match [regex]::Escape($exp) }).Count)) { Write-Log ('WARNING: model does not match model_expect "' + $exp + '"') }
        if (-not $caps.effort) { Write-Log 'WARNING: --effort not supported by this CLI version; effort is unverified.' }
    }
}
