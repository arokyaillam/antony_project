# Ask for Docker Hub username
$username = Read-Host -Prompt "Enter your Docker Hub username"

# Set image name
$imageName = "antony-hft-app"
$tag = "latest"

# Build the image
Write-Host "Building image..."
docker build -t $imageName .

# Tag the image
Write-Host "Tagging image..."
docker tag $imageName "$username/${imageName}:${tag}"

# Push the image
Write-Host "Pushing image to Docker Hub..."
docker push "$username/${imageName}:${tag}"

Write-Host "Done! Image pushed to $username/${imageName}:${tag}"
