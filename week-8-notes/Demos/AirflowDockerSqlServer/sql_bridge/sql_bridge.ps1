$ErrorActionPreference = "Stop"

Import-Module SqlServer

$serverInstance = "LAPTOP-0TBPBTEL"
$databaseName = "AirflowDemoDB"
$listenAddress ="http://+:5055/"

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($listenAddress)
$listener.Start()

Write-Host "======================================================="
Write-Host "SQL Server Windows Authentication Bridge"
Write-Host "======================================================="
Write-Host "Listening at: $listenAddress"
Write-Host "SQL Server:   $serverInstance"
Write-Host "Database:     $databaseName"
Write-Host "Windows user: $([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host "======================================================="

function Write-JsonResponse {
    param(
        [System.Net.HttpListenerContext]$Context,
        [int]$StatusCode,
        [object]$Body
    )

    $json = $Body | ConvertTo-Json -Depth 10 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)

    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "application/json"
    $Context.Response.ContentEncoding = [System.Text.Encoding]::UTF8
    $Context.Response.ContentLength64 = $bytes.Length

    $Context.Response.OutputStream.Write(
        $bytes,
        0,
        $bytes.Length
    )

    $Context.Response.OutputStream.Close()
}

while ($listener.IsListening) {
    try {
        $context = $listener.GetContext()
        $request = $context.Request

        Write-Host "$($request.HttpMethod) $($request.Url.AbsolutePath)"

        if (
            $request.HttpMethod -eq "GET" -and
            $request.Url.AbsolutePath -eq "/health"
        ) {
            $result = Invoke-Sqlcmd `
                -ServerInstance $serverInstance `
                -Database $databaseName `
                -TrustServerCertificate `
                -Query @"
SELECT
    SYSTEM_USER AS LoginName,
    DB_NAME() AS DatabaseName,
    @@SERVERNAME AS ServerName;
"@

            $responseBody = @{
                status       = "healthy"
                login_name   = $result.LoginName
                database     = $result.DatabaseName
                server_name  = $result.ServerName
                windows_user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
            }

            Write-JsonResponse `
                -Context $context `
                -StatusCode 200 `
                -Body $responseBody

            continue
        }

        if (
            $request.HttpMethod -eq "GET" -and
            $request.Url.AbsolutePath -eq "/sales"
        ) {
            $rows = Invoke-Sqlcmd `
                -ServerInstance $serverInstance `
                -Database $databaseName `
                -TrustServerCertificate `
                -Query @"
SELECT
    SaleID,
    ProductName,
    Category,
    Quantity,
    UnitPrice,
    CONVERT(VARCHAR(10), SaleDate, 23) AS SaleDate
FROM dbo.Sales
ORDER BY SaleID;
"@

            $sales = @(
                $rows | ForEach-Object {
                    @{
                        SaleID      = [int]$_.SaleID
                        ProductName = [string]$_.ProductName
                        Category    = [string]$_.Category
                        Quantity    = [int]$_.Quantity
                        UnitPrice   = [decimal]$_.UnitPrice
                        SaleDate    = [string]$_.SaleDate
                    }
                }
            )

            $responseBody = @{
                status    = "success"
                row_count = $sales.Count
                data      = $sales
            }

            Write-JsonResponse `
                -Context $context `
                -StatusCode 200 `
                -Body $responseBody

            continue
        }

        $notFoundBody = @{
            status  = "error"
            message = "Endpoint not found"
        }

        Write-JsonResponse `
            -Context $context `
            -StatusCode 404 `
            -Body $notFoundBody
    }
    catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red

        if ($null -ne $context) {
            $errorBody = @{
                status  = "error"
                message = $_.Exception.Message
            }

            Write-JsonResponse `
                -Context $context `
                -StatusCode 500 `
                -Body $errorBody
        }
    }
}