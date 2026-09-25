# AgentLoop.ps1 - core of the local agent loop (Windows PowerShell 5.1+ / PowerShell 7).
# Keep this file ASCII-only: Windows PowerShell 5.1 reads BOM-less scripts as ANSI.
# All Czech texts live in UTF-8 files under agent-loop/prompts and agent-loop/review-loop.

$ErrorActionPreference = 'Stop'

$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -eq 'Desktop') -or ((Get-Variable -Name IsWindows -ValueOnly -ErrorAction SilentlyContinue) -eq $true)
$script:Root = $null
$script:Cfg = $null
$script:Claude = $null
$script:Git = $null
$script:LogFile = $null

# ---------------------------------------------------------------- basics

function Initialize-Loop {
    param([string]$RepoRoot)
    $script:Root = (Resolve-Path -LiteralPath $RepoRoot).Path
    try { [Console]::OutputEncoding = $script:Utf8 } catch { }
    $cfgPath = Get-RepoPath 'agent-loop/config.json'
    $script:Cfg = Read-Json $cfgPath
    if ($null -eq $script:Cfg) { throw "Missing or invalid $cfgPath" }
    $g = Get-Command git -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $g) { throw 'git not found in PATH' }
    $script:Git = $g.Source
    $logDir = Get-RepoPath '.loop-logs'
    if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $script:LogFile = Join-Path $logDir ('loop-' + (Get-Date).ToString('yyyyMMdd') + '.log')
}

function Get-RepoPath([string]$Rel) {
    return [IO.Path]::GetFullPath([IO.Path]::Combine($script:Root, ($Rel -replace '/', [IO.Path]::DirectorySeparatorChar)))
}

function Get-Now { return (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz') }

function Write-Log([string]$Msg) {
    $line = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') + '  ' + $Msg
    Write-Host $line
    if ($script:LogFile) { try { [IO.File]::AppendAllText($script:LogFile, $line + "`n", $script:Utf8) } catch { } }
}

function Get-Prop($Obj, [string]$Name, $Default = $null) {
    if ($null -eq $Obj) { return $Default }
    if ($Obj -is [System.Collections.IDictionary]) {
        if ($Obj.Contains($Name) -and $null -ne $Obj[$Name]) { return $Obj[$Name] }
        return $Default
    }
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p -or $null -eq $p.Value) { return $Default }
    return $p.Value
}

function Get-Cfg([string]$Name, $Default = $null) { return Get-Prop $script:Cfg $Name $Default }

function Read-Text([string]$Path) { return [IO.File]::ReadAllText($Path, $script:Utf8) }

function Write-Text([string]$Path, [string]$Text) {
    $dir = [IO.Path]::GetDirectoryName($Path)
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [IO.File]::WriteAllText($Path, $Text, $script:Utf8)
}

function Read-Json([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        $t = Read-Text $Path
        if ([string]::IsNullOrWhiteSpace($t)) { return $null }
        return ($t | ConvertFrom-Json)
    } catch { return $null }
}

function Write-Json([string]$Path, $Obj) {
    Write-Text $Path ((ConvertTo-Json -InputObject $Obj -Depth 30) + "`n")
}

function Limit-Text([string]$Text, [int]$MaxKb) {
    if ($null -eq $Text) { return $null }
    $max = $MaxKb * 1024
    if ($Text.Length -le $max) { return $Text }
    return $Text.Substring(0, $max) + "`n... [truncated, " + $Text.Length + " chars total]"
}

function ConvertTo-PlainObject($Obj) {
    # PSCustomObject -> ordered hashtable (recursive), so objects can be modified freely.
    if ($null -eq $Obj) { return $null }
    if ($Obj -is [string] -or $Obj -is [ValueType]) { return $Obj }
    if ($Obj -is [System.Collections.IDictionary]) {
        $h = [ordered]@{}
        foreach ($k in $Obj.Keys) { $h[$k] = ConvertTo-PlainObject $Obj[$k] }
        return $h
    }
    if ($Obj -is [System.Collections.IEnumerable]) {
        $list = New-Object System.Collections.ArrayList
        foreach ($i in $Obj) { [void]$list.Add((ConvertTo-PlainObject $i)) }
        return ,$list.ToArray()
    }
    $h = [ordered]@{}
    foreach ($p in $Obj.PSObject.Properties) { $h[$p.Name] = ConvertTo-PlainObject $p.Value }
    return $h
}

# ---------------------------------------------------------------- processes

function Format-Arg([string]$s) {
    if ($s -eq '') { return '""' }
    if ($s -notmatch '[\s"]') { return $s }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('"')
    $bs = 0
    foreach ($c in $s.ToCharArray()) {
        if ($c -eq '\') { $bs++; continue }
        if ($c -eq '"') { [void]$sb.Append(('\' * ($bs * 2 + 1)) + '"'); $bs = 0; continue }
        if ($bs -gt 0) { [void]$sb.Append('\' * $bs); $bs = 0 }
        [void]$sb.Append($c)
    }
    [void]$sb.Append('\' * ($bs * 2))
    [void]$sb.Append('"')
    return $sb.ToString()
}

function Stop-ProcessTree($Proc) {
    try {
        if ($script:OnWindows) {
            & taskkill.exe /PID $Proc.Id /T /F 2>&1 | Out-Null
        } else {
            try { $Proc.Kill($true) } catch { $Proc.Kill() }
        }
    } catch { }
}

function Invoke-Native {
    param(
        [string]$File,
        [string[]]$Arguments = @(),
        [string]$StdIn = $null,
        [int]$TimeoutSec = 0,
        [scriptblock]$OnTick = $null,
        [int]$TickSec = 30,
        [hashtable]$Env = $null,
        [scriptblock]$OnStart = $null,
        [scriptblock]$OnLine = $null
    )
    $argStr = (@($Arguments) | ForEach-Object { Format-Arg ([string]$_) }) -join ' '
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $ext = [IO.Path]::GetExtension($File).ToLowerInvariant()
    if ($script:OnWindows -and ($ext -eq '.cmd' -or $ext -eq '.bat')) {
        $psi.FileName = $env:ComSpec
        $psi.Arguments = '/d /s /c "' + (Format-Arg $File) + ' ' + $argStr + '"'
    } else {
        $psi.FileName = $File
        $psi.Arguments = $argStr
    }
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8
    $psi.StandardErrorEncoding = $script:Utf8
    $psi.WorkingDirectory = $script:Root
    if ($Env) { foreach ($k in $Env.Keys) { $psi.EnvironmentVariables[$k] = [string]$Env[$k] } }

    $p = [System.Diagnostics.Process]::Start($psi)
    if ($OnStart) { try { & $OnStart $p } catch { } }
    $outTask = $null
    if ($null -eq $OnLine) { $outTask = $p.StandardOutput.ReadToEndAsync() }
    $errTask = $p.StandardError.ReadToEndAsync()
    try {
        if ($StdIn) {
            $bytes = $script:Utf8.GetBytes($StdIn)
            $p.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
            $p.StandardInput.BaseStream.Flush()
        }
    } catch { }
    try { $p.StandardInput.Close() } catch { }

    $timedOut = $false
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    if ($OnLine) {
        # streaming mode: hand every stdout line to $OnLine as it arrives
        $sb = New-Object System.Text.StringBuilder
        $lastTick = 0.0
        $lineTask = $p.StandardOutput.ReadLineAsync()
        while ($true) {
            if ($lineTask.Wait(500)) {
                $line = $lineTask.Result
                if ($null -eq $line) { break }
                [void]$sb.AppendLine($line)
                try { & $OnLine $line } catch { }
                $lineTask = $p.StandardOutput.ReadLineAsync()
            }
            $el = $sw.Elapsed.TotalSeconds
            if ($OnTick -and ($el - $lastTick) -ge $TickSec) { $lastTick = $el; try { & $OnTick } catch { } }
            if (-not $timedOut -and $TimeoutSec -gt 0 -and $el -ge $TimeoutSec) { $timedOut = $true; Stop-ProcessTree $p }
        }
        $p.WaitForExit()
        $out = $sb.ToString()
        $err = $errTask.Result
        return [pscustomobject]@{
            Code = $p.ExitCode; Out = $out; Err = $err; TimedOut = $timedOut; Seconds = [int]$sw.Elapsed.TotalSeconds
        }
    }
    if ($TimeoutSec -le 0 -and $null -eq $OnTick) {
        $p.WaitForExit()
    } else {
        $tickMs = [Math]::Max(1000, $TickSec * 1000)
        while (-not $p.WaitForExit($tickMs)) {
            if ($OnTick) { try { & $OnTick } catch { } }
            if ($TimeoutSec -gt 0 -and $sw.Elapsed.TotalSeconds -ge $TimeoutSec) {
                $timedOut = $true
                Stop-ProcessTree $p
                break
            }
        }
        $p.WaitForExit()
    }
    $out = $outTask.Result
    $err = $errTask.Result
    return [pscustomobject]@{
        Code = $p.ExitCode; Out = $out; Err = $err; TimedOut = $timedOut; Seconds = [int]$sw.Elapsed.TotalSeconds
    }
}

function Invoke-Git {
    param([string[]]$GitArgs, [switch]$AllowFail)
    $r = Invoke-Native -File $script:Git -Arguments (@('-c', 'core.quotepath=false') + $GitArgs)
    if ($r.Code -ne 0 -and -not $AllowFail) {
        throw ('git ' + ($GitArgs -join ' ') + ' failed (' + $r.Code + '): ' + $r.Err.Trim())
    }
    return $r
}

function Get-GitBranch { return (Invoke-Git @('rev-parse', '--abbrev-ref', 'HEAD')).Out.Trim() }

function Test-Remote {
    $remote = Get-Cfg 'remote' 'origin'
    $r = Invoke-Git @('remote') -AllowFail
    return ($r.Out -split "`n" | ForEach-Object { $_.Trim() }) -contains $remote
}

function Get-GitChanges {
    # Returns list of @{ Code; Path } for tracked changes and untracked files (ignored excluded).
    $r = Invoke-Git @('status', '--porcelain=v1', '-z', '-uall')
    $items = New-Object System.Collections.ArrayList
    $parts = $r.Out.Split([char]0)
    $i = 0
    while ($i -lt $parts.Length) {
        $e = $parts[$i]
        if ($e.Length -lt 4) { $i++; continue }
        $code = $e.Substring(0, 2)
        $path = $e.Substring(3)
        [void]$items.Add([pscustomobject]@{ Code = $code; Path = $path })
        if ($code[0] -eq 'R' -or $code[0] -eq 'C') {
            $i++
            if ($i -lt $parts.Length -and $parts[$i]) { [void]$items.Add([pscustomobject]@{ Code = $code; Path = $parts[$i] }) }
        }
        $i++
    }
    return $items.ToArray()
}

function Test-TreeClean { return (@(Get-GitChanges).Count -eq 0) }

function Invoke-Commit([string]$Subject, [string]$Body, [string[]]$Paths) {
    if ($Paths -and $Paths.Count -gt 0) {
        Invoke-Git (@('add', '-A', '--') + $Paths) | Out-Null
    } else {
        Invoke-Git @('add', '-A') | Out-Null
    }
    $staged = Invoke-Git @('diff', '--cached', '--quiet') -AllowFail
    if ($staged.Code -eq 0) { return $false }
    $msgFile = Get-RepoPath '.git/LOOP_COMMIT_MSG'
    $msg = $Subject
    if ($Body) { $msg += "`n`n" + $Body }
    Write-Text $msgFile ($msg + "`n")
    Invoke-Git @('commit', '-q', '-F', $msgFile) | Out-Null
    return $true
}

function Sync-Pull {
    # Rebase local commits onto the remote. Returns $true when in sync (or no remote).
    if (-not (Test-Remote)) { return $true }
    $remote = Get-Cfg 'remote' 'origin'
    $branch = Get-GitBranch
    $f = Invoke-Git @('fetch', '-q', $remote) -AllowFail
    if ($f.Code -ne 0) { Write-Log ('fetch failed: ' + $f.Err.Trim()); return $false }
    $ref = $remote + '/' + $branch
    $has = Invoke-Git @('rev-parse', '--verify', '-q', $ref) -AllowFail
    if ($has.Code -ne 0) { return $true }
    $rb = Invoke-Git @('rebase', '-q', $ref) -AllowFail
    if ($rb.Code -ne 0) {
        Invoke-Git @('rebase', '--abort') -AllowFail | Out-Null
        Write-Log ('rebase onto ' + $ref + ' failed, local history kept: ' + $rb.Err.Trim())
        return $false
    }
    return $true
}

function Sync-Push {
    if (-not (Get-Cfg 'push' $true)) { return $true }
    if (-not (Test-Remote)) { return $true }
    $remote = Get-Cfg 'remote' 'origin'
    $branch = Get-GitBranch
    for ($i = 0; $i -lt 2; $i++) {
        $p = Invoke-Git @('push', '-q', $remote, ('HEAD:refs/heads/' + $branch)) -AllowFail
        if ($p.Code -eq 0) { return $true }
        Write-Log ('push failed: ' + $p.Err.Trim())
        if (-not (Sync-Pull)) { return $false }
    }
    return $false
}

# ---------------------------------------------------------------- lock and stop

function Test-StopFile { return (Test-Path -LiteralPath (Get-RepoPath 'STOP')) }

function Enter-LoopLock {
    $lp = Get-RepoPath '.loop.lock'
    $l = Read-Json $lp
    if ($l) {
        $alive = $false
        $lpid = [int](Get-Prop $l 'pid' 0)
        if ($lpid -gt 0) { $alive = [bool](Get-Process -Id $lpid -ErrorAction SilentlyContinue) }
        $hb = Get-Prop $l 'heartbeat' $null
        $stale = $true
        if ($hb) {
            $age = ((Get-Date) - [DateTimeOffset]::Parse($hb).LocalDateTime).TotalMinutes
            $stale = $age -gt (2 * [int](Get-Cfg 'default_max_minutes' 60) + 10)
        }
        if ($alive -and -not $stale -and $lpid -ne $PID) { throw ('Loop already running (pid ' + $lpid + '). Lock: ' + $lp) }
        Write-Log ('Taking over stale lock (pid ' + $lpid + ')')
        if (-not $alive) { Stop-OrphanAgent $l }
    }
    Update-LoopLock
}

$script:ChildPid = 0

function Update-LoopLock {
    Write-Json (Get-RepoPath '.loop.lock') ([ordered]@{ pid = $PID; child_pid = $script:ChildPid; host = [Environment]::MachineName; heartbeat = (Get-Now) })
}

function Stop-OrphanAgent($Lock) {
    # An agent process started by a dead loop may still be editing files: stop it before taking over.
    $cp = [int](Get-Prop $Lock 'child_pid' 0)
    if ($cp -le 0) { return }
    $proc = Get-Process -Id $cp -ErrorAction SilentlyContinue
    if ($null -eq $proc) { return }
    if ($proc.ProcessName -notmatch '(?i)claude|node|cmd|bash|sh') { return }
    Write-Log ('Stopping orphaned agent process ' + $cp + ' (' + $proc.ProcessName + ')')
    Stop-ProcessTree $proc
}

function Exit-LoopLock {
    $lp = Get-RepoPath '.loop.lock'
    $l = Read-Json $lp
    if ($l -and [int](Get-Prop $l 'pid' 0) -eq $PID) { Remove-Item -LiteralPath $lp -Force -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------- tasks

$script:TaskFolders = @('inbox', 'active', 'done')

function Get-AllTasks {
    $list = New-Object System.Collections.ArrayList
    foreach ($f in $script:TaskFolders) {
        $dir = Get-RepoPath ('tasks/' + $f)
        if (-not (Test-Path -LiteralPath $dir)) { continue }
        foreach ($file in @(Get-ChildItem -LiteralPath $dir -Filter '*.json' -File | Sort-Object Name)) {
            $t = Read-Json $file.FullName
            [void]$list.Add([pscustomobject]@{ Folder = $f; File = $file.FullName; Name = $file.Name; Task = $t })
        }
    }
    return $list.ToArray()
}

function Get-TaskNumber([string]$Id) {
    # Regular ids are TASK-0001 .. TASK-999999; longer numbers (timestamps from the static form) are temporary.
    if ($Id -match '^TASK-(\d{4,6})$') { return [int]$Matches[1] }
    return -1
}

function Get-NextTaskId {
    $max = 0
    foreach ($t in @(Get-AllTasks)) {
        $n = Get-TaskNumber ([IO.Path]::GetFileNameWithoutExtension($t.Name))
        if ($n -gt $max) { $max = $n }
        $n2 = Get-TaskNumber ([string](Get-Prop $t.Task 'id' ''))
        if ($n2 -gt $max) { $max = $n2 }
    }
    return ('TASK-{0:D4}' -f ($max + 1))
}

function Select-NextTask {
    $all = @(Get-AllTasks)
    foreach ($folder in @('active', 'inbox')) {
        $c = @($all | Where-Object { $_.Folder -eq $folder })
        if ($c.Count -eq 0) { continue }
        $sorted = @($c | Sort-Object -Property @{ Expression = { [int](Get-Prop $_.Task 'priority' 100) } }, @{ Expression = { [string](Get-Prop $_.Task 'created_at' '') } }, @{ Expression = { $_.Name } })
        return $sorted[0]
    }
    return $null
}

function Get-TaskDir([string]$Id) { return 'runs/' + $Id }

function Read-TaskState([string]$Id) {
    $s = Read-Json (Get-RepoPath ((Get-TaskDir $Id) + '/state.json'))
    if ($null -eq $s) { return $null }
    return (ConvertTo-PlainObject $s)
}

function Save-TaskState([string]$Id, $State) {
    $State['updated_at'] = Get-Now
    Write-Json (Get-RepoPath ((Get-TaskDir $Id) + '/state.json')) $State
}

function ConvertTo-StringList($v) {
    if ($null -eq $v) { return @() }
    if ($v -is [string]) {
        return @($v -split '[,;\n]' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }
    return @($v | ForEach-Object { [string]$_ } | Where-Object { $_ })
}

function Resolve-TaskFields($Task) {
    # Normalized view of a task file with defaults. Model and effort always come from config.
    $t = ConvertTo-PlainObject $Task
    if ($null -eq $t) { $t = [ordered]@{} }
    $mode = [string](Get-Prop $t 'mode' 'spec')
    return [ordered]@{
        id          = [string](Get-Prop $t 'id' '')
        title       = [string](Get-Prop $t 'title' '')
        mode        = $mode
        goal        = [string](Get-Prop $t 'goal' '')
        done_when   = [string](Get-Prop $t 'done_when' '')
        inputs      = @(ConvertTo-StringList (Get-Prop $t 'inputs' $null))
        scope_allow = @(ConvertTo-StringList (Get-Prop $t 'scope_allow' $null))
        scope_deny  = @(ConvertTo-StringList (Get-Prop $t 'scope_deny' $null))
        max_rounds  = [int](Get-Prop $t 'max_rounds' (Get-Cfg 'default_max_rounds' 5))
        max_minutes = [int](Get-Prop $t 'max_minutes' (Get-Cfg 'default_max_minutes' 60))
        priority    = [int](Get-Prop $t 'priority' 100)
        restart     = [bool](Get-Prop $t 'restart' $false)
        notes       = [string](Get-Prop $t 'notes' '')
        created_at  = [string](Get-Prop $t 'created_at' '')
    }
}

function Test-TaskValid($F) {
    $errs = @()
    if ($F.mode -notin @('spec', 'code')) { $errs += 'mode must be spec or code' }
    if (-not $F.title) { $errs += 'title is empty' }
    if (-not $F.goal) { $errs += 'goal is empty' }
    if (-not $F.done_when) { $errs += 'done_when is empty' }
    if ($F.scope_allow.Count -eq 0) { $errs += 'scope_allow is empty' }
    if ($F.max_rounds -lt 1) { $errs += 'max_rounds < 1' }
    if ($F.max_minutes -lt 1) { $errs += 'max_minutes < 1' }
    return $errs
}

function Move-TaskFile($Entry, [string]$ToFolder, [string]$NewName = $null) {
    $name = $Entry.Name
    if ($NewName) { $name = $NewName }
    $fromRel = 'tasks/' + $Entry.Folder + '/' + $Entry.Name
    $toRel = 'tasks/' + $ToFolder + '/' + $name
    $toAbs = Get-RepoPath $toRel
    $dir = [IO.Path]::GetDirectoryName($toAbs)
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $tracked = (Invoke-Git @('ls-files', '--error-unmatch', '--', $fromRel) -AllowFail).Code -eq 0
    if ($tracked) { Invoke-Git @('mv', '-f', '--', $fromRel, $toRel) | Out-Null }
    else { Move-Item -LiteralPath (Get-RepoPath $fromRel) -Destination $toAbs -Force }
    return [pscustomobject]@{ Folder = $ToFolder; File = $toAbs; Name = $name; Task = $Entry.Task }
}

# ---------------------------------------------------------------- scope

function ConvertTo-GlobRegex([string]$Glob) {
    $g = ($Glob -replace '\\', '/').Trim()
    if ($g.EndsWith('/')) { $g += '**' }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('^')
    $i = 0
    while ($i -lt $g.Length) {
        $c = $g[$i]
        if ($c -eq '*') {
            if ($i + 1 -lt $g.Length -and $g[$i + 1] -eq '*') {
                if ($i + 2 -lt $g.Length -and $g[$i + 2] -eq '/') { [void]$sb.Append('(?:.*/)?'); $i += 3; continue }
                [void]$sb.Append('.*'); $i += 2; continue
            }
            [void]$sb.Append('[^/]*'); $i++; continue
        }
        if ($c -eq '?') { [void]$sb.Append('[^/]'); $i++; continue }
        [void]$sb.Append([regex]::Escape([string]$c)); $i++
    }
    [void]$sb.Append('$')
    return $sb.ToString()
}

function Test-PathMatch([string]$Path, [string[]]$Globs) {
    $p = $Path -replace '\\', '/'
    foreach ($g in $Globs) {
        if (-not $g) { continue }
        if ($p -match (ConvertTo-GlobRegex $g)) { return $true }
        # a directory pattern without wildcard also covers its content
        if ($g -notmatch '[\*\?]' -and $p.StartsWith(($g.TrimEnd('/') + '/'))) { return $true }
    }
    return $false
}

function Test-InScope([string]$Path, $F, [string]$TaskDir) {
    $p = $Path -replace '\\', '/'
    if ($p.StartsWith($TaskDir + '/')) { return $true }
    if ($p -eq 'agent-loop/a1/data.js') { return $true }   # written by the runner during the round (live view)
    if (Test-PathMatch $p $F.scope_deny) { return $false }
    return (Test-PathMatch $p $F.scope_allow)
}

function Undo-RoundChanges($Changes, [string]$KeepPrefix, [string]$DiscardDir, [string[]]$KeepFiles = @()) {
    # Revert every change except files under $KeepPrefix and $KeepFiles. Copies of discarded content go to $DiscardDir.
    foreach ($c in $Changes) {
        $p = $c.Path -replace '\\', '/'
        if ($p.StartsWith($KeepPrefix + '/')) { continue }
        if ($KeepFiles -contains $p) { continue }
        $abs = Get-RepoPath $p
        if (Test-Path -LiteralPath $abs -PathType Leaf) {
            $copy = Get-RepoPath ($DiscardDir + '/' + $p)
            $cd = [IO.Path]::GetDirectoryName($copy)
            if (-not (Test-Path -LiteralPath $cd)) { New-Item -ItemType Directory -Path $cd -Force | Out-Null }
            Copy-Item -LiteralPath $abs -Destination $copy -Force
        }
        if ($c.Code -eq '??') {
            Remove-Item -LiteralPath $abs -Force -ErrorAction SilentlyContinue
        } else {
            Invoke-Git @('checkout', '-q', 'HEAD', '--', $p) -AllowFail | Out-Null
        }
    }
}

# ---------------------------------------------------------------- claude

$script:ClaudeCaps = $null

function Resolve-Claude {
    $cmd = [string](Get-Cfg 'claude_command' 'claude')
    if (Test-Path -LiteralPath $cmd -PathType Leaf) { $path = (Resolve-Path -LiteralPath $cmd).Path }
    else {
        $c = @(Get-Command $cmd -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)
        if ($c.Count -eq 0) { throw ('claude CLI not found: ' + $cmd) }
        $path = $c[0].Source
    }
    if ($path.ToLowerInvariant().EndsWith('.ps1')) {
        foreach ($alt in @('.cmd', '.exe')) {
            $cand = [IO.Path]::ChangeExtension($path, $alt)
            if (Test-Path -LiteralPath $cand) { $path = $cand; break }
        }
    }
    $script:Claude = $path
    return $path
}

function Get-ClaudeCaps {
    if ($script:ClaudeCaps) { return $script:ClaudeCaps }
    if (-not $script:Claude) { Resolve-Claude | Out-Null }
    $h = Invoke-Native -File $script:Claude -Arguments @('--help') -TimeoutSec 120
    $v = Invoke-Native -File $script:Claude -Arguments @('--version') -TimeoutSec 60
    $txt = $h.Out + $h.Err
    $script:ClaudeCaps = [ordered]@{
        path    = $script:Claude
        version = ($v.Out + $v.Err).Trim()
        effort  = [bool]($txt -match '--effort')
        bare    = [bool]($txt -match '--bare')
    }
    return $script:ClaudeCaps
}

function Get-ClaudeArgs([string]$Mode) {
    $caps = Get-ClaudeCaps
    $a = @('-p', '--model', [string](Get-Cfg 'model' 'fable'))
    if ($caps.effort) { $a += @('--effort', [string](Get-Cfg 'effort' 'max')) }
    if ((Get-Cfg 'use_bare' $false) -and $caps.bare) { $a += '--bare' }
    $tools = [string](Get-Prop (Get-Cfg 'tools') $Mode 'Read,Edit,Write,Glob,Grep')
    $a += @('--allowedTools', $tools, '--permission-mode', 'acceptEdits', '--output-format', 'stream-json', '--verbose')
    foreach ($x in @(Get-Cfg 'extra_args' @())) { if ($x) { $a += [string]$x } }
    return ,$a
}

function ConvertFrom-ClaudeOutput([string]$Out) {
    if (-not $Out) { return $null }
    # stream-json: take the last line that is the final result event
    $lines = @($Out -split "`n" | Where-Object { $_.TrimStart().StartsWith('{') })
    for ($i = $lines.Count - 1; $i -ge 0; $i--) {
        if ($lines[$i] -match '"type"\s*:\s*"result"') {
            try { return ($lines[$i] | ConvertFrom-Json) } catch { }
        }
    }
    $s = $Out.IndexOf('{'); $e = $Out.LastIndexOf('}')
    if ($s -lt 0 -or $e -le $s) { return $null }
    try { return ($Out.Substring($s, $e - $s + 1) | ConvertFrom-Json) } catch { return $null }
}

# ---------------------------------------------------------------- live log (stream-json -> readable lines)

function Compress-Line($Text, [int]$Max) {
    if ($null -eq $Text) { return '' }
    $s = ([string]$Text -replace '\s+', ' ').Trim()
    if ($s.Length -gt $Max) { $s = $s.Substring(0, $Max) + ' ...' }
    return $s
}

function Format-ToolInput($In) {
    if ($null -eq $In) { return '' }
    $parts = @()
    foreach ($k in @('file_path', 'path', 'pattern', 'glob', 'pages', 'offset', 'limit', 'command', 'description', 'url', 'query')) {
        $v = Get-Prop $In $k $null
        if ($null -ne $v -and [string]$v -ne '') { $parts += ($k + '=' + (Compress-Line $v 160)) }
    }
    if ($parts.Count -eq 0) { try { return (Compress-Line (ConvertTo-Json -InputObject $In -Depth 5 -Compress) 160) } catch { return '' } }
    return ($parts -join '  ')
}

function Get-ToolResultText($C) {
    $c2 = Get-Prop $C 'content' ''
    if ($c2 -is [string]) { return $c2 }
    $txt = @()
    foreach ($x in @($c2)) { $v = Get-Prop $x 'text' $null; if ($v) { $txt += [string]$v } }
    return ($txt -join ' ')
}

function Format-StreamEvent([string]$Line) {
    if (-not $Line -or -not $Line.TrimStart().StartsWith('{')) { return $null }
    $e = $null
    try { $e = $Line | ConvertFrom-Json } catch { return $null }
    $ts = (Get-Date).ToString('HH:mm:ss')
    $out = New-Object System.Collections.ArrayList
    $type = [string](Get-Prop $e 'type' '')
    if ($type -eq 'system' -and [string](Get-Prop $e 'subtype' '') -eq 'init') {
        [void]$out.Add($ts + '  == start, model ' + [string](Get-Prop $e 'model' '?'))
    } elseif ($type -eq 'assistant') {
        foreach ($c in @(Get-Prop (Get-Prop $e 'message' $null) 'content' @())) {
            $ct = [string](Get-Prop $c 'type' '')
            if ($ct -eq 'text') {
                $tx = Compress-Line (Get-Prop $c 'text' '') 600
                if ($tx) { [void]$out.Add($ts + '  ' + $tx) }
            } elseif ($ct -eq 'tool_use') {
                [void]$out.Add($ts + '  > ' + [string](Get-Prop $c 'name' '?') + '  ' + (Format-ToolInput (Get-Prop $c 'input' $null)))
            } elseif ($ct -eq 'thinking') {
                $tx = Compress-Line (Get-Prop $c 'thinking' '') 300
                if ($tx) { [void]$out.Add($ts + '  ~ ' + $tx) }
            }
        }
    } elseif ($type -eq 'user') {
        foreach ($c in @(Get-Prop (Get-Prop $e 'message' $null) 'content' @())) {
            if ([string](Get-Prop $c 'type' '') -eq 'tool_result' -and (Get-Prop $c 'is_error' $false)) {
                [void]$out.Add($ts + '  x ' + (Compress-Line (Get-ToolResultText $c) 300))
            }
        }
    } elseif ($type -eq 'result') {
        $s = $ts + '  == end: ' + [string](Get-Prop $e 'subtype' '') + ', turns ' + [string](Get-Prop $e 'num_turns' '?') + ', cost $' + [string](Get-Prop $e 'total_cost_usd' '?')
        if (Get-Prop $e 'is_error' $false) { $s += ', ERROR: ' + (Compress-Line (Get-Prop $e 'result' '') 300) }
        [void]$out.Add($s)
    }
    if ($out.Count -eq 0) { return $null }
    return ($out.ToArray() -join "`n")
}

# ---------------------------------------------------------------- one round

function Format-Template([string]$Text, [hashtable]$Map) {
    foreach ($k in $Map.Keys) { $Text = $Text.Replace('{{' + $k + '}}', [string]$Map[$k]) }
    return $Text
}

function Format-List($Items, [string]$Empty = '- -') {
    $i = @($Items)
    if ($i.Count -eq 0) { return $Empty }
    return (($i | ForEach-Object { '- `' + $_ + '`' }) -join "`n")
}

function New-RoundPrompt($F, [int]$Round, [int]$LastRound, [string]$TaskDir, [string]$RoundDir, [string]$PrevRoundDir) {
    $prompts = Get-Cfg 'prompts'
    $common = Read-Text (Get-RepoPath ([string](Get-Prop $prompts 'common' 'agent-loop/prompts/common.md')))
    $modeP = Read-Text (Get-RepoPath ([string](Get-Prop $prompts $F.mode 'agent-loop/review-loop/review.md')))
    $tpl = Read-Text (Get-RepoPath 'agent-loop/prompts/context.template.md')
    $S = Read-Json (Get-RepoPath 'agent-loop/prompts/strings.json')
    $stateNote = ''
    if (-not (Test-Path -LiteralPath (Get-RepoPath ($TaskDir + '/state.md')))) { $stateNote = [string](Get-Prop $S 'state_missing' '') }
    $prevResult = [string](Get-Prop $S 'no_prev_result' '-'); $prevDiff = [string](Get-Prop $S 'no_prev_diff' '-')
    if ($PrevRoundDir) {
        $prevResult = '`' + $PrevRoundDir + '/result.json`'
        if (Test-Path -LiteralPath (Get-RepoPath ($PrevRoundDir + '/diff.patch'))) { $prevDiff = '`' + $PrevRoundDir + '/diff.patch`' }
    }
    $notes = $F.notes
    if (-not $notes) { $notes = [string](Get-Prop $S 'no_notes' '-') }
    $empty = [string](Get-Prop $S 'empty_list' '- -')
    $ctx = Format-Template $tpl @{
        ID = $F.id; TITLE = $F.title; MODE = $F.mode; ROUND = $Round; LAST_ROUND = $LastRound; DATE = (Get-Now)
        GOAL = $F.goal; DONE_WHEN = $F.done_when; INPUTS = (Format-List $F.inputs $empty)
        SCOPE_ALLOW = (Format-List $F.scope_allow $empty); SCOPE_DENY = (Format-List $F.scope_deny $empty)
        TASK_DIR = $TaskDir; ROUND_DIR = $RoundDir; STATE_NOTE = $stateNote
        PREV_RESULT = $prevResult; PREV_DIFF = $prevDiff; NOTES = $notes
    }
    Write-Text (Get-RepoPath ($RoundDir + '/context.md')) $ctx
    return ($common.TrimEnd() + "`n`n---`n`n" + $modeP.TrimEnd() + "`n`n---`n`n" + $ctx)
}

function Invoke-AgentRound {
    param($F, [int]$Round, [int]$LastRound, $State)
    $id = $F.id
    $taskDir = Get-TaskDir $id
    $roundDir = $taskDir + '/round-' + ('{0:D2}' -f $Round)
    $prevDir = $null
    if ($Round -gt 1) {
        $pd = $taskDir + '/round-' + ('{0:D2}' -f ($Round - 1))
        if (Test-Path -LiteralPath (Get-RepoPath $pd)) { $prevDir = $pd }
    }
    $absRound = Get-RepoPath $roundDir
    if (Test-Path -LiteralPath $absRound) { Remove-Item -LiteralPath $absRound -Recurse -Force }
    New-Item -ItemType Directory -Path $absRound -Force | Out-Null

    $prompt = New-RoundPrompt $F $Round $LastRound $taskDir $roundDir $prevDir
    $caps = Get-ClaudeCaps
    $cargs = Get-ClaudeArgs $F.mode
    $model = [string](Get-Cfg 'model' 'fable')
    $effort = [string](Get-Cfg 'effort' 'max')
    $envVars = @{ 'CLAUDE_CODE_EFFORT_LEVEL' = $effort }

    $State['phase'] = 'running'
    $State['current_round'] = $Round
    $State['heartbeat'] = Get-Now
    Save-TaskState $id $State
    Update-LoopLock

    $started = Get-Now
    $retries = [int](Get-Cfg 'retries' 3)
    $attempt = 0
    $r = $null
    $fatal = $null
    # invoked from Invoke-Native; $State and $id resolve through dynamic scope
    $tick = { $State['heartbeat'] = Get-Now; Save-TaskState $id $State; Update-LoopLock; try { Update-Report } catch { } }
    $liveAbs = Get-RepoPath ($roundDir + '/live.log')
    $onLine = { param($l) $s = Format-StreamEvent $l; if ($s) { [IO.File]::AppendAllText($liveAbs, $s + "`n", $script:Utf8) } }
    while ($true) {
        $attempt++
        Write-Log ("$id r$Round attempt $attempt ($model, effort $effort)")
        $r = Invoke-Native -File $script:Claude -Arguments $cargs -StdIn $prompt -TimeoutSec ($F.max_minutes * 60) -OnTick $tick -TickSec ([int](Get-Cfg 'heartbeat_seconds' 30)) -Env $envVars -OnLine $onLine -OnStart { param($pr) $script:ChildPid = $pr.Id; Update-LoopLock }
        $script:ChildPid = 0
        Update-LoopLock
        Write-Text (Get-RepoPath ($roundDir + '/stdout.log')) ($r.Out + $(if ($r.Err) { "`n--- stderr ---`n" + $r.Err } else { '' }))
        if ($r.Code -eq 0 -or $r.TimedOut) { break }
        $jj = ConvertFrom-ClaudeOutput $r.Out
        $api = [int](Get-Prop $jj 'api_error_status' 0)
        $apiCode = [string](Get-Prop $jj 'api_error_code' '')
        if ($api -eq 401 -or $api -eq 403 -or $apiCode -eq 'credits_required') {
            # waiting does not help: login expired or spend limit / credits exhausted
            $fatal = ('API ' + $api + ' ' + $apiCode + ': ' + [string](Get-Prop $jj 'result' '')).Trim()
            Write-Log ("$id r$Round fatal API error, no retry: " + $fatal)
            break
        }
        if ($attempt -ge $retries) { break }
        $sleep = [int](Get-Cfg 'retry_sleep_seconds' 3600)
        Write-Log ("$id r$Round failed (exit $($r.Code)); retry in $sleep s")
        $State['phase'] = 'retry_wait'
        Save-TaskState $id $State
        $until = (Get-Date).AddSeconds($sleep)
        while ((Get-Date) -lt $until) {
            if (Test-StopFile) { break }
            Start-Sleep -Seconds ([Math]::Min(30, [Math]::Max(1, ($until - (Get-Date)).TotalSeconds)))
            Update-LoopLock
        }
        if (Test-StopFile) { break }
        $State['phase'] = 'running'
    }
    $ended = Get-Now
    $j = ConvertFrom-ClaudeOutput $r.Out
    $usage = Get-Prop $j 'usage' $null
    $modelUsage = Get-Prop $j 'modelUsage' $null
    $actual = @()
    if ($modelUsage) { $actual = @($modelUsage.PSObject.Properties | ForEach-Object { $_.Name }) }
    $resultText = [string](Get-Prop $j 'result' '')
    if ($resultText) { Write-Text (Get-RepoPath ($roundDir + '/output.md')) $resultText }

    $result = Read-Json (Get-RepoPath ($roundDir + '/result.json'))
    $status = [string](Get-Prop $result 'status' '')
    $noResult = ($status -notin @('DONE', 'CONTINUE', 'BLOCKED'))

    # model check: every model reported by the CLI must match model_expect, otherwise the round is discarded
    $expect = [string](Get-Cfg 'model_expect' '')
    $badModels = @($actual | Where-Object { $expect -and ($_ -notmatch [regex]::Escape($expect)) })
    $mismatch = [bool]($expect -and (($badModels.Count -gt 0) -or ($r.Code -eq 0 -and -not $r.TimedOut -and $actual.Count -eq 0)))
    $mismatchDetail = ''
    if ($mismatch) {
        $seen = ($actual -join ', '); if (-not $seen) { $seen = 'unknown (CLI reported no model)' }
        $mismatchDetail = 'expected "' + $expect + '", CLI used: ' + $seen
        Write-Log ("$id r$Round MODEL MISMATCH, round discarded: " + $mismatchDetail)
    }

    # scope check
    $changes = @(Get-GitChanges)
    $violations = @($changes | Where-Object { -not (Test-InScope $_.Path $F $taskDir) } | ForEach-Object { $_.Path })
    if ($violations.Count -gt 0 -and -not $mismatch) {
        Write-Log ("$id r$Round scope violation, round discarded: " + ($violations -join ', '))
    }
    if ($violations.Count -gt 0 -or $mismatch) {
        Undo-RoundChanges $changes $roundDir ($roundDir + '/discarded') @(($taskDir + '/state.json'), 'agent-loop/a1/data.js')
    }

    $meta = [ordered]@{
        task = $id; round = $Round; mode = $F.mode
        requested_model = $model; requested_effort = $effort
        actual_models = $actual
        effort_verified = [bool]$caps.effort
        claude_version = $caps.version
        bare = [bool]((Get-Cfg 'use_bare' $false) -and $caps.bare)
        input_tokens = (Get-Prop $usage 'input_tokens' $null)
        output_tokens = (Get-Prop $usage 'output_tokens' $null)
        cache_read_tokens = (Get-Prop $usage 'cache_read_input_tokens' $null)
        cache_creation_tokens = (Get-Prop $usage 'cache_creation_input_tokens' $null)
        cost_usd = (Get-Prop $j 'total_cost_usd' $null)
        num_turns = (Get-Prop $j 'num_turns' $null)
        is_error = (Get-Prop $j 'is_error' $null)
        session_id = (Get-Prop $j 'session_id' $null)
        started_at = $started; ended_at = $ended; duration_s = $r.Seconds
        exit_code = $r.Code; attempts = $attempt; timed_out = $r.TimedOut; fatal_error = $fatal
        no_result = $noResult
        scope_violation = ($violations.Count -gt 0); scope_violations = $violations
        model_mismatch = $mismatch; model_mismatch_detail = $mismatchDetail
        changed_files = @()
    }

    # stage everything, save the diff of work files (without runner files of this round)
    Invoke-Git @('add', '-A') | Out-Null
    $work = Invoke-Git @('diff', '--cached', '--name-only', '--', '.', (':(exclude)' + $taskDir + '/**'), ':(exclude)agent-loop/a1/data.js') -AllowFail
    $meta['changed_files'] = @($work.Out -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $diff = Invoke-Git @('diff', '--cached', '--stat', '-p', '--', '.', (':(exclude)' + $roundDir + '/**'), (':(exclude)' + $taskDir + '/state.json'), ':(exclude)agent-loop/a1/data.js') -AllowFail
    if ($diff.Out) { Write-Text (Get-RepoPath ($roundDir + '/diff.patch')) (Limit-Text $diff.Out ([int](Get-Cfg 'diff_max_kb' 200))) }
    Write-Json (Get-RepoPath ($roundDir + '/meta.json')) $meta

    return [pscustomobject]@{ Meta = $meta; Result = $result; Status = $status; NoResult = $noResult; Failed = ($r.Code -ne 0 -and -not $r.TimedOut -and -not $fatal); Fatal = $fatal }
}

function Format-Tokens($n) {
    if ($null -eq $n) { return '?' }
    $d = [double]$n
    if ($d -ge 1000) { return ('{0:0.0}k' -f ($d / 1000)).Replace(',', '.') }
    return [string][int]$d
}

# ---------------------------------------------------------------- task run

function Invoke-Task($Entry) {
    $F = Resolve-TaskFields $Entry.Task

    if ($Entry.Folder -eq 'inbox') {
        # validate and (re)number
        $idOk = ((Get-TaskNumber $F.id) -gt 0) -and ($Entry.Name -eq ($F.id + '.json'))
        if ($idOk) {
            $dups = @(Get-AllTasks | Where-Object { $_.File -ne $Entry.File -and ([IO.Path]::GetFileNameWithoutExtension($_.Name) -eq $F.id) })
            if ($dups.Count -gt 0 -and -not (Test-Path -LiteralPath (Get-RepoPath ((Get-TaskDir $F.id) + '/state.json')))) { $idOk = $false }
            if ($dups.Count -gt 0 -and (Test-Path -LiteralPath (Get-RepoPath ((Get-TaskDir $F.id) + '/state.json')))) {
                # a restarted task that still has a stale copy elsewhere: drop the old copy
                foreach ($d in $dups) { Invoke-Git @('rm', '-q', '-f', '--', ('tasks/' + $d.Folder + '/' + $d.Name)) -AllowFail | Out-Null }
            }
        }
        $raw = ConvertTo-PlainObject $Entry.Task
        if ($null -eq $raw) { $raw = [ordered]@{} }
        if (-not $idOk) {
            $newId = Get-NextTaskId
            Write-Log ("renumbering " + $Entry.Name + " -> " + $newId)
            $raw['id'] = $newId
            $F.id = $newId
        }
        if (-not (Get-Prop $raw 'created_at' $null)) { $raw['created_at'] = Get-Now }
        $errs = @(Test-TaskValid $F)
        $restartFromScratch = $F.restart
        if ($raw.Contains('restart')) { $raw.Remove('restart') }
        Write-Json $Entry.File $raw
        $Entry = [pscustomobject]@{ Folder = $Entry.Folder; File = $Entry.File; Name = $Entry.Name; Task = $raw }
        $dest = 'active'
        if ($errs.Count -gt 0) { $dest = 'done' }
        $moved = Move-TaskFile $Entry $dest ($F.id + '.json')
        $taskDir = Get-TaskDir $F.id
        $state = Read-TaskState $F.id
        if ($errs.Count -gt 0) {
            $state = [ordered]@{ task = $F.id; status = 'invalid'; errors = $errs; round = 0; ended_at = (Get-Now) }
            Save-TaskState $F.id $state
            Invoke-Commit ($F.id + ' invalid task: ' + ($errs -join '; ')) '' @() | Out-Null
            Write-Log ($F.id + ' invalid: ' + ($errs -join '; '))
            Sync-Push | Out-Null
            return $true
        }
        if ($restartFromScratch -and $state) {
            $arch = $taskDir + '/archive-' + (Get-Date).ToString('yyyyMMddHHmmss')
            New-Item -ItemType Directory -Path (Get-RepoPath $arch) -Force | Out-Null
            foreach ($item in @(Get-ChildItem -LiteralPath (Get-RepoPath $taskDir) | Where-Object { $_.Name -notlike 'archive-*' })) {
                Move-Item -LiteralPath $item.FullName -Destination (Join-Path (Get-RepoPath $arch) $item.Name) -Force
            }
            $state = $null
        }
        if ($null -eq $state) {
            $state = [ordered]@{ task = $F.id; status = 'running'; phase = 'queued'; round = 0; run_start_round = 0; started_at = (Get-Now); ended_at = $null; heartbeat = (Get-Now); last_status = $null; last_summary = $null; push_failed = $false }
        } else {
            $state['status'] = 'running'; $state['run_start_round'] = [int](Get-Prop $state 'round' 0); $state['ended_at'] = $null
        }
        Save-TaskState $F.id $state
        Invoke-Commit ($F.id + ' start [' + $F.mode + '] ' + $F.title) '' @() | Out-Null
        Sync-Push | Out-Null
        $Entry = $moved
    }

    $F = Resolve-TaskFields $Entry.Task
    $id = $F.id
    $state = Read-TaskState $id
    if ($null -eq $state) {
        $state = [ordered]@{ task = $id; status = 'running'; phase = 'queued'; round = 0; run_start_round = 0; started_at = (Get-Now); heartbeat = (Get-Now); push_failed = $false }
    }
    $state['status'] = 'running'
    $startRound = [int](Get-Prop $state 'run_start_round' 0)
    $lastRound = $startRound + $F.max_rounds
    $final = $null

    while ($null -eq $final) {
        $round = [int](Get-Prop $state 'round' 0) + 1
        if ($round -gt $lastRound) { $final = 'max_rounds'; break }
        if (Test-StopFile) { Write-Log 'STOP file present, pausing task'; $state['phase'] = 'paused'; Save-TaskState $id $state; return $false }
        if (-not (Test-TreeClean)) {
            $state['phase'] = 'paused'; Save-TaskState $id $state
            Write-Log 'Working tree is not clean; round not started. Commit or revert your changes.'
            return $false
        }
        $res = Invoke-AgentRound -F $F -Round $round -LastRound $lastRound -State $state
        $m = $res.Meta
        $state['round'] = $round
        $state['phase'] = 'between_rounds'
        $state['heartbeat'] = Get-Now
        $state['last_status'] = $res.Status
        $state['last_summary'] = [string](Get-Prop $res.Result 'summary' '')
        if ($res.Fatal) { $state['status'] = 'stopped'; $state['phase'] = 'paused'; $state['stop_reason'] = $res.Fatal }
        elseif ($res.Failed) { $final = 'failed' }
        elseif ($m.model_mismatch) { $state['status'] = 'model_mismatch'; $state['phase'] = 'paused'; $state['model_mismatch'] = $m.model_mismatch_detail }
        elseif ($m.scope_violation) { }
        elseif ($res.Status -eq 'DONE') { $final = 'done' }
        elseif ($res.Status -eq 'BLOCKED') { $final = 'blocked' }
        if ($null -eq $final -and $round -ge $lastRound) { $final = 'max_rounds' }
        if ($final) { $state['status'] = $final; $state['phase'] = 'ended'; $state['ended_at'] = Get-Now }
        Save-TaskState $id $state
        Update-Report

        $st = $res.Status; if (-not $st) { $st = 'NO_RESULT' }
        if ($m.scope_violation) { $st = 'SCOPE_VIOLATION' }
        if ($res.Fatal) {
            $st = 'API_ERROR'
            Write-Text (Get-RepoPath 'STOP') ('API_ERROR ' + $id + ' r' + $round + ': ' + $res.Fatal + "`n")
            Update-Report
        }
        if ($m.model_mismatch) {
            $st = 'MODEL_MISMATCH'
            # stop the whole loop; STOP carries the reason and is shown in A1
            Write-Text (Get-RepoPath 'STOP') ('MODEL_MISMATCH ' + $id + ' r' + $round + ': ' + $m.model_mismatch_detail + "`n")
            Update-Report
        }
        if ($res.Failed) { $st = 'FAILED' }
        $fnd = Get-Prop $res.Result 'findings' $null
        $mdl = ($m.actual_models -join '+')
        if (-not $mdl) { $mdl = $m.requested_model }
        $subject = '{0} r{1:D2} [{2}] model={3} effort={4} status={5} B/S/D={6}/{7}/{8} tok={9}/{10} min={11}' -f $id, $round, $F.mode, $mdl, $m.requested_effort, $st, (Get-Prop $fnd 'blocking' '-'), (Get-Prop $fnd 'medium' '-'), (Get-Prop $fnd 'minor' '-'), (Format-Tokens $m.input_tokens), (Format-Tokens $m.output_tokens), [int]($m.duration_s / 60)
        Invoke-Commit $subject ([string](Get-Prop $res.Result 'summary' '')) @() | Out-Null
        $ok = Sync-Push
        if (-not $ok -and -not $state['push_failed']) { $state['push_failed'] = $true; Save-TaskState $id $state; Invoke-Commit ($id + ' push failed flag') '' @() | Out-Null }
        Write-Log ("$id r$round -> $st")
        if ($res.Fatal) {
            Write-Log ('LOOP STOPPED: ' + $res.Fatal + ' -- fix it (login / usage credits), then run: start-loop.cmd resume')
            return $false
        }
        if ($m.model_mismatch) {
            Write-Log ('LOOP STOPPED: ' + $m.model_mismatch_detail + '. Fix agent-loop/config.json or the CLI, then run: start-loop.cmd resume')
            return $false
        }
    }

    $state['status'] = $final; $state['phase'] = 'ended'
    if (-not (Get-Prop $state 'ended_at' $null)) { $state['ended_at'] = Get-Now }
    Save-TaskState $id $state
    $cur = @(Get-AllTasks | Where-Object { $_.Folder -eq 'active' -and $_.Name -eq ($id + '.json') })
    if ($cur.Count -gt 0) { Move-TaskFile $cur[0] 'done' | Out-Null }
    Update-Report
    Invoke-Commit ($id + ' end status=' + $final) '' @() | Out-Null
    Sync-Push | Out-Null
    Write-Log ("$id finished: $final")
    return $true
}

# ---------------------------------------------------------------- recovery

function Add-InboxFiles {
    # Task files dropped into tasks/inbox locally (untracked) are committed so the tree stays clean.
    $ch = @(Get-GitChanges)
    if ($ch.Count -eq 0) { return }
    $inbox = @($ch | Where-Object { $_.Code -eq '??' -and ($_.Path -replace '\\', '/') -like 'tasks/inbox/*.json' })
    if ($inbox.Count -ne $ch.Count) { return }
    Invoke-Commit ('task: add ' + (($inbox | ForEach-Object { [IO.Path]::GetFileName($_.Path) }) -join ', ')) '' @($inbox | ForEach-Object { $_.Path }) | Out-Null
    Sync-Push | Out-Null
}

function Repair-Interrupted {
    # A round interrupted by a crash or reboot leaves uncommitted files. Keep the in-scope work,
    # discard the rest and commit it as an interrupted round.
    foreach ($e in @(Get-AllTasks | Where-Object { $_.Folder -eq 'active' })) {
        $F = Resolve-TaskFields $e.Task
        $s = Read-TaskState $F.id
        if ($null -eq $s) { continue }
        $phase = [string](Get-Prop $s 'phase' '')
        if ($phase -notin @('running', 'retry_wait')) { continue }
        $cur = [int](Get-Prop $s 'current_round' ([int](Get-Prop $s 'round' 0) + 1))
        $taskDir = Get-TaskDir $F.id
        $roundDir = $taskDir + '/round-' + ('{0:D2}' -f $cur)
        $ch = @(Get-GitChanges)
        $viol = @($ch | Where-Object { -not (Test-InScope $_.Path $F $taskDir) })
        if ($viol.Count -gt 0) { Undo-RoundChanges $ch $roundDir ($roundDir + '/discarded') @(($taskDir + '/state.json'), 'agent-loop/a1/data.js') }
        $res = Read-Json (Get-RepoPath ($roundDir + '/result.json'))
        $rst = [string](Get-Prop $res 'status' '')
        $s['round'] = $cur
        $s['phase'] = 'between_rounds'
        $s['last_status'] = 'INTERRUPTED'
        if ($viol.Count -eq 0 -and $rst -eq 'DONE') {
            # the agent finished and decided to end before the loop died
            $s['last_status'] = 'DONE'; $s['status'] = 'done'; $s['phase'] = 'ended'; $s['ended_at'] = Get-Now
            Move-TaskFile $e 'done' | Out-Null
        }
        Save-TaskState $F.id $s
        Invoke-Commit ('{0} r{1:D2} [{2}] status=INTERRUPTED result={3} (recovered after restart of the loop)' -f $F.id, $cur, $F.mode, $(if ($rst) { $rst } else { 'none' })) '' @() | Out-Null
        Sync-Push | Out-Null
        Write-Log ($F.id + ' round ' + $cur + ' was interrupted; recovered')
    }
}

# ---------------------------------------------------------------- main loop

function Start-Loop([switch]$Once) {
    Enter-LoopLock
    try {
        Resolve-Claude | Out-Null
        $caps = Get-ClaudeCaps
        Write-Log ("claude: " + $caps.path + ' | ' + $caps.version + ' | --effort supported: ' + $caps.effort + ' | --bare supported: ' + $caps.bare)
        if (-not $caps.effort) { Write-Log 'WARNING: this claude CLI has no --effort flag; effort is only requested via CLAUDE_CODE_EFFORT_LEVEL and marked unverified.' }
        Repair-Interrupted
        while ($true) {
            Update-LoopLock
            if (Test-StopFile) { Write-Log ('STOP file present, loop ends. ' + (Read-Text (Get-RepoPath 'STOP')).Trim()); break }
            Add-InboxFiles
            $clean = Test-TreeClean
            if ($clean) { Sync-Pull | Out-Null }
            $entry = Select-NextTask
            $progressed = $false
            if ($entry -and -not $clean) {
                Write-Log 'Working tree is not clean; waiting (commit or revert local changes).'
            } elseif ($entry) {
                try { $progressed = [bool](Invoke-Task $entry) }
                catch { Write-Log ('ERROR in task ' + $entry.Name + ': ' + $_.Exception.Message + ' @ ' + $_.InvocationInfo.PositionMessage) }
                if ($Once) { break }
                if ($progressed) { continue }
            }
            if ($Once) { break }
            $poll = [int](Get-Cfg 'poll_seconds' 300)
            $until = (Get-Date).AddSeconds($poll)
            while ((Get-Date) -lt $until -and -not (Test-StopFile)) { Start-Sleep -Seconds 5 }
        }
    } finally {
        Exit-LoopLock
    }
}

# ---------------------------------------------------------------- local task commands

function New-LoopTask {
    param([string]$Title, [string]$Goal, [string]$DoneWhen, [string[]]$ScopeAllow, [string]$Mode = 'spec', [string[]]$Inputs = @(), [string[]]$ScopeDeny = @(), [int]$MaxRounds = 0, [int]$MaxMinutes = 0, [int]$Priority = 100, [string]$Notes = '')
    if (-not (Test-TreeClean)) { throw 'Working tree is not clean.' }
    Sync-Pull | Out-Null
    $id = Get-NextTaskId
    if ($MaxRounds -le 0) { $MaxRounds = [int](Get-Cfg 'default_max_rounds' 5) }
    if ($MaxMinutes -le 0) { $MaxMinutes = [int](Get-Cfg 'default_max_minutes' 60) }
    $t = [ordered]@{
        id = $id; title = $Title; mode = $Mode; goal = $Goal; done_when = $DoneWhen
        inputs = @($Inputs); scope_allow = @($ScopeAllow); scope_deny = @($ScopeDeny)
        max_rounds = $MaxRounds; max_minutes = $MaxMinutes; priority = $Priority; notes = $Notes; created_at = (Get-Now)
    }
    $errs = @(Test-TaskValid (Resolve-TaskFields $t))
    if ($errs.Count -gt 0) { throw ('Invalid task: ' + ($errs -join '; ')) }
    Write-Json (Get-RepoPath ('tasks/inbox/' + $id + '.json')) $t
    Update-Report
    Invoke-Commit ('task: ' + $id + ' ' + $Title) '' @() | Out-Null
    Sync-Push | Out-Null
    Write-Log ('created ' + $id)
    return $id
}

function Restart-LoopTask([string]$Id, [switch]$FromScratch) {
    if (-not (Test-TreeClean)) { throw 'Working tree is not clean.' }
    Sync-Pull | Out-Null
    $e = @(Get-AllTasks | Where-Object { $_.Name -eq ($Id + '.json') -and $_.Folder -ne 'inbox' })
    if ($e.Count -eq 0) { throw ('Task not found in active/done: ' + $Id) }
    $raw = ConvertTo-PlainObject $e[0].Task
    $raw['restart'] = [bool]$FromScratch
    Write-Json $e[0].File $raw
    Move-TaskFile $e[0] 'inbox' | Out-Null
    $s = Read-TaskState $Id
    if ($s) { $s['status'] = 'queued'; $s['phase'] = 'queued'; Save-TaskState $Id $s }
    Update-Report
    Invoke-Commit ('task: restart ' + $Id + $(if ($FromScratch) { ' from scratch' } else { '' })) '' @() | Out-Null
    Sync-Push | Out-Null
    Write-Log ('requeued ' + $Id)
}

# ---------------------------------------------------------------- report for A1

function Read-TextOrNull([string]$Rel, [int]$MaxKb) {
    $abs = Get-RepoPath $Rel
    if (-not (Test-Path -LiteralPath $abs -PathType Leaf)) { return $null }
    return (Limit-Text (Read-Text $abs) $MaxKb)
}

function Get-LiveTail([string]$Rel, [int]$MaxKb) {
    # the end of the live log is the interesting part
    $abs = Get-RepoPath $Rel
    if (-not (Test-Path -LiteralPath $abs -PathType Leaf)) { return $null }
    $t = Read-Text $abs
    $max = $MaxKb * 1024
    if ($t.Length -le $max) { return $t }
    $cut = $t.Substring($t.Length - $max)
    $nl = $cut.IndexOf("`n")
    if ($nl -ge 0) { $cut = $cut.Substring($nl + 1) }
    return ('... [' + ($t.Length - $cut.Length) + " chars earlier]`n" + $cut)
}

function Get-CommitMap {
    $map = @{}
    $r = Invoke-Git @('log', '-n', '5000', '--format=%H%x09%cI%x09%s') -AllowFail
    if ($r.Code -ne 0) { return $map }
    foreach ($line in ($r.Out -split "`n")) {
        $p = $line.Split("`t")
        if ($p.Length -lt 3) { continue }
        $s = $p[2]
        if ($s -match '^(TASK-\d+) r(\d+) ') {
            $k = $Matches[1] + '|' + [int]$Matches[2]
            if (-not $map.ContainsKey($k)) { $map[$k] = [ordered]@{ hash = $p[0]; date = $p[1]; subject = $s } }
        } elseif ($s -match '^(TASK-\d+) (start|end)') {
            $k = $Matches[1] + '|' + $Matches[2]
            if (-not $map.ContainsKey($k)) { $map[$k] = [ordered]@{ hash = $p[0]; date = $p[1]; subject = $s } }
        }
    }
    return $map
}

function Get-TaskWarnings($Task, $State, $Rounds) {
    $w = New-Object System.Collections.ArrayList
    $F = Resolve-TaskFields $Task
    $expect = [string](Get-Cfg 'model_expect' 'fable')
    $status = [string](Get-Prop $State 'status' 'queued')
    $noChangeStreak = 0
    foreach ($r in $Rounds) {
        $m = $r.meta
        if ($null -eq $m) { continue }
        $n = $r.round
        $am = @(Get-Prop $m 'actual_models' @())
        if ((Get-Prop $m 'model_mismatch' $false) -or ($am.Count -gt 0 -and $expect -and @($am | Where-Object { $_ -notmatch [regex]::Escape($expect) }).Count -gt 0)) {
            [void]$w.Add([ordered]@{ code = 'MODEL_MISMATCH'; detail = "r${n}: " + [string](Get-Prop $m 'model_mismatch_detail' (($am -join ', ') + " (expected $expect)")) + ' - round discarded, loop stopped' })
        }
        if (-not (Get-Prop $m 'effort_verified' $false)) { [void]$w.Add([ordered]@{ code = 'EFFORT_UNVERIFIED'; detail = "r${n}: CLI without --effort" }) }
        if (Get-Prop $m 'scope_violation' $false) { [void]$w.Add([ordered]@{ code = 'SCOPE_VIOLATION'; detail = "r$n discarded: " + (@(Get-Prop $m 'scope_violations' @()) -join ', ') }) }
        if (Get-Prop $m 'fatal_error' $null) { [void]$w.Add([ordered]@{ code = 'API_ERROR'; detail = "r${n}: " + [string](Get-Prop $m 'fatal_error' '') + ' - loop stopped' }) }
        if (Get-Prop $m 'timed_out' $false) { [void]$w.Add([ordered]@{ code = 'TIMEOUT'; detail = "r$n exceeded max_minutes" }) }
        elseif (Get-Prop $m 'no_result' $false) { [void]$w.Add([ordered]@{ code = 'NO_RESULT'; detail = "r$n wrote no valid result.json" }) }
        if ($null -eq (Get-Prop $m 'cost_usd' $null) -and $null -eq (Get-Prop $m 'input_tokens' $null)) { [void]$w.Add([ordered]@{ code = 'COST_UNKNOWN'; detail = "r${n}: no usage data" }) }
        if (@(Get-Prop $m 'changed_files' @()).Count -eq 0) { $noChangeStreak++ } else { $noChangeStreak = 0 }
        if ($noChangeStreak -eq 2) { [void]$w.Add([ordered]@{ code = 'NO_CHANGE'; detail = "two rounds in a row without changes (up to r$n)" }) }
    }
    if ($status -eq 'running') {
        $hb = Get-Prop $State 'heartbeat' $null
        if ($hb) {
            $age = ((Get-Date) - [DateTimeOffset]::Parse($hb).LocalDateTime).TotalMinutes
            if ($age -gt ($F.max_minutes + 10)) { [void]$w.Add([ordered]@{ code = 'STUCK'; detail = ('heartbeat ' + [int]$age + ' min old') }) }
        }
    }
    if ($status -eq 'max_rounds') { [void]$w.Add([ordered]@{ code = 'MAX_ROUNDS'; detail = 'stopped after N rounds without DONE' }) }
    if ($status -eq 'failed') { [void]$w.Add([ordered]@{ code = 'FAILED'; detail = 'claude run failed after retries' }) }
    if ($status -eq 'blocked') { [void]$w.Add([ordered]@{ code = 'BLOCKED'; detail = 'agent ended with BLOCKED' }) }
    if ($status -eq 'invalid') { [void]$w.Add([ordered]@{ code = 'INVALID'; detail = (@(Get-Prop $State 'errors' @()) -join '; ') }) }
    if (Get-Prop $State 'push_failed' $false) { [void]$w.Add([ordered]@{ code = 'PUSH_FAILED'; detail = 'git push failed at least once' }) }
    if ($Rounds.Count -gt 0) {
        $req = @(Get-Prop $Rounds[$Rounds.Count - 1].result 'requests' @())
        if ($req.Count -gt 0) { [void]$w.Add([ordered]@{ code = 'REQUESTS'; detail = ($req -join ' | ') }) }
    }
    return $w.ToArray()
}

function Update-Report {
    $textKb = [int](Get-Cfg 'report_text_max_kb' 20)
    $diffKb = [int](Get-Cfg 'report_diff_max_kb' 60)
    $commits = Get-CommitMap
    $tasks = New-Object System.Collections.ArrayList
    foreach ($e in @(Get-AllTasks)) {
        $raw = ConvertTo-PlainObject $e.Task
        $id = [IO.Path]::GetFileNameWithoutExtension($e.Name)
        $tid = [string](Get-Prop $raw 'id' '')
        if ($tid) { $id = $tid }
        $taskDir = Get-TaskDir $id
        $state = Read-TaskState $id
        if ($null -eq $state) { $state = [ordered]@{ status = 'queued' } }
        $rounds = New-Object System.Collections.ArrayList
        $absDir = Get-RepoPath $taskDir
        if (Test-Path -LiteralPath $absDir) {
            foreach ($d in @(Get-ChildItem -LiteralPath $absDir -Directory | Where-Object { $_.Name -match '^round-\d+$' } | Sort-Object Name)) {
                $n = [int]($d.Name.Substring(6))
                $rd = $taskDir + '/' + $d.Name
                $c = $null
                $ck = $id + '|' + $n
                if ($commits.ContainsKey($ck)) { $c = $commits[$ck] }
                [void]$rounds.Add([ordered]@{
                    round   = $n
                    meta    = (ConvertTo-PlainObject (Read-Json (Get-RepoPath ($rd + '/meta.json'))))
                    result  = (ConvertTo-PlainObject (Read-Json (Get-RepoPath ($rd + '/result.json'))))
                    notes   = (Read-TextOrNull ($rd + '/notes.md') $textKb)
                    output  = (Read-TextOrNull ($rd + '/output.md') $textKb)
                    diff    = (Read-TextOrNull ($rd + '/diff.patch') $diffKb)
                    live    = (Get-LiveTail ($rd + '/live.log') $textKb)
                    commit  = $c
                })
            }
        }
        $roundsArr = $rounds.ToArray()
        $tot = [ordered]@{ rounds = $roundsArr.Count; input_tokens = 0; output_tokens = 0; cost_usd = 0.0; duration_s = 0; cost_known = $true }
        foreach ($r in $roundsArr) {
            $m = $r.meta
            if ($null -eq $m) { continue }
            $tot.input_tokens += [double](Get-Prop $m 'input_tokens' 0)
            $tot.output_tokens += [double](Get-Prop $m 'output_tokens' 0)
            $cst = Get-Prop $m 'cost_usd' $null
            if ($null -eq $cst) { $tot.cost_known = $false } else { $tot.cost_usd += [double]$cst }
            $tot.duration_s += [int](Get-Prop $m 'duration_s' 0)
        }
        $startC = $null; if ($commits.ContainsKey($id + '|start')) { $startC = $commits[$id + '|start'] }
        $endC = $null; if ($commits.ContainsKey($id + '|end')) { $endC = $commits[$id + '|end'] }
        [void]$tasks.Add([ordered]@{
            id       = $id
            folder   = $e.Folder
            file     = ('tasks/' + $e.Folder + '/' + $e.Name)
            task     = $raw
            state    = $state
            state_md = (Read-TextOrNull ($taskDir + '/state.md') $textKb)
            rounds   = $roundsArr
            totals   = $tot
            warnings = @(Get-TaskWarnings $raw $state $roundsArr)
            commits  = [ordered]@{ start = $startC; end = $endC }
        })
    }
    $lock = Read-Json (Get-RepoPath '.loop.lock')
    $data = [ordered]@{
        generated_at = (Get-Now)
        repo_url     = [string](Get-Cfg 'repo_url' '')
        branch       = (Get-GitBranch)
        model        = [string](Get-Cfg 'model' '')
        effort       = [string](Get-Cfg 'effort' '')
        runner       = [ordered]@{ heartbeat = (Get-Prop $lock 'heartbeat' $null); host = (Get-Prop $lock 'host' $null); stop_file = (Test-StopFile); stop_reason = $(if (Test-StopFile) { (Read-Text (Get-RepoPath 'STOP')).Trim() } else { $null }) }
        tasks        = $tasks.ToArray()
    }
    $json = ConvertTo-Json -InputObject $data -Depth 30 -Compress
    Write-Text (Get-RepoPath 'agent-loop/a1/data.js') ('window.LOOP_DATA = ' + $json + ";`n")
}
