# PowerShell script to push Docker images to GCP Artifact Registry
param (
    [string]$RegistryUrl = "us-west1-docker.pkg.dev/citric-kit-489316-g6/charan-ar"
)

$IMAGES = @(
    "capstone-app-cart-service:latest",
    "capstone-app-payment-service:latest",
    "capstone-app-product-service:latest",
    "capstone-app-ui-service:latest",
    "capstone-app-user-service:latest"
)

Write-Host "GCP Artifact Registry Push Script"
Write-Host "Registry: $RegistryUrl"
Write-Host "Images to push: $($IMAGES.Count)"
Write-Host ""

try {
    Write-Host "Configuring Docker authentication for GCP..."
    gcloud auth configure-docker us-west1-docker.pkg.dev

    $failedImages = @()
    $successfulImages = @()

    foreach ($image in $IMAGES) {
        $imageName = $image.Split(":")[0]
        $imageTag = $image.Split(":")[1]
        $gcpFullImage = "$RegistryUrl/$($imageName):$imageTag"
        
        Write-Host "Processing: $image"
        Write-Host "  Tagging as: $gcpFullImage"
        
        docker tag $image $gcpFullImage
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Failed to tag image"
            $failedImages += $image
            continue
        }
        
        Write-Host "  Pushing to registry..."
        docker push $gcpFullImage
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Successfully pushed"
            $successfulImages += $image
        }
        else {
            Write-Host "  Failed to push image"
            $failedImages += $image
        }
        
        Write-Host ""
    }

    Write-Host "================================"
    Write-Host "PUSH SUMMARY"
    Write-Host "================================"
    Write-Host "Successful: $($successfulImages.Count)/$($IMAGES.Count)"
    
    foreach ($img in $successfulImages) {
        Write-Host "  [OK] $img"
    }
    
    if ($failedImages.Count -gt 0) {
        Write-Host "Failed: $($failedImages.Count)"
        foreach ($img in $failedImages) {
            Write-Host "  [FAIL] $img"
        }
        exit 1
    }
    else {
        Write-Host "All images pushed successfully!"
        exit 0
    }
}
catch {
    Write-Host "Error: $_"
    exit 1
}
