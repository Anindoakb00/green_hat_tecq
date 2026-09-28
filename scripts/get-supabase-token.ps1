param(
    [Parameter(Mandatory = $true)] [string] $PublishableKey,
    [Parameter(Mandatory = $true)] [string] $Email,
    [Parameter(Mandatory = $true)] [string] $Password
)

$body = @{ email = $Email; password = $Password } | ConvertTo-Json
$headers = @{ apikey = $PublishableKey; "Content-Type" = "application/json" }
$response = Invoke-RestMethod -Uri "https://tjgdclyupxksqcwwlqoy.supabase.co/auth/v1/token?grant_type=password" -Method Post -Headers $headers -Body $body
$response.access_token
