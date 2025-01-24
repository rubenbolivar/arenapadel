#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔄 Actualizando repositorio...${NC}"

# Asegurar que estamos en la rama main
git checkout main

# Agregar todos los cambios (excluyendo los que están en .gitignore)
git add .

# Crear commit con timestamp
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "🚀 Production update: $timestamp"

# Push al repositorio
git push origin main

echo -e "${GREEN}✅ Repositorio actualizado exitosamente${NC}"
