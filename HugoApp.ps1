Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Fix Encoding and Language for Git/Hugo Output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:LANG = "en_US.UTF-8"
$env:LC_ALL = "en_US.UTF-8"

$Form = New-Object System.Windows.Forms.Form
$Form.Text = "Hugo Manager"
$Form.Size = New-Object System.Drawing.Size(400,450)
$Form.StartPosition = "CenterScreen"
$Form.FormBorderStyle = 'FixedDialog'
$Form.MaximizeBox = $false

# Working Directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

# --- Title Label ---
$TitleLabel = New-Object System.Windows.Forms.Label
$TitleLabel.Location = New-Object System.Drawing.Point(20,20)
$TitleLabel.Size = New-Object System.Drawing.Size(350,30)
$TitleLabel.Text = "🚀 Hugo Site Manager"
$TitleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$Form.Controls.Add($TitleLabel)

# --- Create Post Section ---
$CreateLabel = New-Object System.Windows.Forms.Label
$CreateLabel.Location = New-Object System.Drawing.Point(20,70)
$CreateLabel.Size = New-Object System.Drawing.Size(350,20)
$CreateLabel.Text = "1. Create New Post (e.g. my-new-post.md):"
$Form.Controls.Add($CreateLabel)

$PostNameBox = New-Object System.Windows.Forms.TextBox
$PostNameBox.Location = New-Object System.Drawing.Point(20,95)
$PostNameBox.Size = New-Object System.Drawing.Size(240,20)
$Form.Controls.Add($PostNameBox)

$CreateBtn = New-Object System.Windows.Forms.Button
$CreateBtn.Location = New-Object System.Drawing.Point(270,93)
$CreateBtn.Size = New-Object System.Drawing.Size(90,25)
$CreateBtn.Text = "Create"
$CreateBtn.BackColor = [System.Drawing.Color]::LightBlue
$Form.Controls.Add($CreateBtn)

$CreateBtn.Add_Click({
    $postName = $PostNameBox.Text.Trim()
    if ([string]::IsNullOrWhiteSpace($postName)) {
        [System.Windows.Forms.MessageBox]::Show("Please enter a valid post name.", "Error", 0, [System.Windows.Forms.MessageBoxIcon]::Warning)
        return
    }
    
    # Ensure it ends with .md
    if (-not $postName.EndsWith(".md")) {
        $postName += ".md"
    }

    $LogBox.AppendText("`r`n[INFO] Creating post: $postName...`r`n")
    
    # Run hugo new
    $output = hugo new content/posts/$postName 2>&1
    $LogBox.AppendText("$output`r`n")
    $LogBox.AppendText("[SUCCESS] Post created!`r`n")
    
    # Try to open the file
    $filePath = Join-Path -Path $scriptPath -ChildPath "content\posts\$postName"
    if (Test-Path $filePath) {
        Invoke-Item $filePath
    }
    
    $PostNameBox.Text = ""
})

# --- Push Section ---
$PushLabel = New-Object System.Windows.Forms.Label
$PushLabel.Location = New-Object System.Drawing.Point(20,140)
$PushLabel.Size = New-Object System.Drawing.Size(350,20)
$PushLabel.Text = "2. Push to GitHub Pages:"
$Form.Controls.Add($PushLabel)

$CommitLabel = New-Object System.Windows.Forms.Label
$CommitLabel.Location = New-Object System.Drawing.Point(20,165)
$CommitLabel.Size = New-Object System.Drawing.Size(90,20)
$CommitLabel.Text = "Commit Msg:"
$Form.Controls.Add($CommitLabel)

$CommitMsgBox = New-Object System.Windows.Forms.TextBox
$CommitMsgBox.Location = New-Object System.Drawing.Point(110,162)
$CommitMsgBox.Size = New-Object System.Drawing.Size(250,20)
$CommitMsgBox.Text = "Update posts"
$Form.Controls.Add($CommitMsgBox)

$PushBtn = New-Object System.Windows.Forms.Button
$PushBtn.Location = New-Object System.Drawing.Point(20,195)
$PushBtn.Size = New-Object System.Drawing.Size(340,35)
$PushBtn.Text = "🚀 Push to GitHub"
$PushBtn.BackColor = [System.Drawing.Color]::LightGreen
$PushBtn.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$Form.Controls.Add($PushBtn)

$PushBtn.Add_Click({
    $commitMsg = $CommitMsgBox.Text.Trim()
    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = "Update posts"
    }

    $LogBox.AppendText("`r`n[INFO] Adding files...`r`n")
    $Form.Refresh()
    
    $addOut = git add . 2>&1
    $LogBox.AppendText("$addOut`r`n")
    
    $LogBox.AppendText("[INFO] Committing changes...`r`n")
    $Form.Refresh()
    
    $commitOut = git commit -m "$commitMsg" 2>&1
    $LogBox.AppendText("$commitOut`r`n")
    
    $LogBox.AppendText("[INFO] Pushing to GitHub...`r`n")
    $Form.Refresh()
    
    $pushOut = git push 2>&1
    $LogBox.AppendText("$pushOut`r`n")
    
    $LogBox.AppendText("=============`r`n")
    $LogBox.AppendText("[SUCCESS] Code pushed successfully!`r`n")
    $CommitMsgBox.Text = "Update posts"
    
    [System.Windows.Forms.MessageBox]::Show("Push completed successfully!", "Success", 0, [System.Windows.Forms.MessageBoxIcon]::Information)
})

# --- Log Box Section ---
$LogLabel = New-Object System.Windows.Forms.Label
$LogLabel.Location = New-Object System.Drawing.Point(20,245)
$LogLabel.Size = New-Object System.Drawing.Size(350,20)
$LogLabel.Text = "Logs:"
$Form.Controls.Add($LogLabel)

$LogBox = New-Object System.Windows.Forms.TextBox
$LogBox.Location = New-Object System.Drawing.Point(20,265)
$LogBox.Size = New-Object System.Drawing.Size(340,120)
$LogBox.Multiline = $true
$LogBox.ScrollBars = "Vertical"
$LogBox.ReadOnly = $true
$LogBox.BackColor = [System.Drawing.Color]::Black
$LogBox.ForeColor = [System.Drawing.Color]::LimeGreen
$LogBox.Font = New-Object System.Drawing.Font("Consolas", 8)
$LogBox.Text = "App Ready. Welcome to Hugo Manager!`r`n"
$Form.Controls.Add($LogBox)

# --- Show Form ---
$Form.Topmost = $true
$Form.Add_Shown({$Form.Activate()})
[void]$Form.ShowDialog()
