$dirs = @(
    "app\api\routes",
    "app\core",
    "app\models",
    "app\services",
    "tests"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir
}