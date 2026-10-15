# INICIO EN WINDOWS — MariaCM34

## Lo único que tienes que preparar

1. Instala [ChatGPT para Windows](https://chatgpt.com/download/) y abre **Codex**, o usa Codex si ya aparece en tu app. Inicia sesión con ChatGPT.
2. Comprueba que Git, Python y Node estén disponibles en PowerShell:

   ```powershell
   git --version
   python --version
   node --version
   ```

3. Descomprime este ZIP en una carpeta personal, por ejemplo `C:\Dev\MariaCM34.github.io` (NO dentro de una carpeta del trabajo o TIWORKS).
4. En el sitio de GitHub, con tu sesión `MariaCM34`, crea un repositorio **público** exactamente `MariaCM34.github.io` (preferiblemente vacío: sin auto-README). Esta operación debe hacerse con tu sesión de esa cuenta.
5. Desde PowerShell dentro de la carpeta descomprimida:

   ```powershell
   git init -b main
   git add .
   git commit -m "chore: initialize portfolio sprint"
   git remote add origin https://github.com/MariaCM34/MariaCM34.github.io.git
   git push -u origin main
   ```

   Si Git pide credenciales, autentícate en `MariaCM34`. No pegues tokens en ChatGPT ni en el repositorio.

## Ejecutar tres hilos sin colisión

**Forma preferida:** en Codex abre la carpeta y crea tres tareas independientes en worktrees (si la interfaz lo ofrece). Copia cada prompt desde `prompts/` al hilo correspondiente. Elige ramas `feat/ask-your-data`, `feat/energypulse`, `feat/modernize-studio` y paths exclusivos.

**Alternativa Git sin soporte visual de worktrees:** después del commit inicial, en PowerShell desde el repositorio:

```powershell
# Desde la carpeta raíz del repo
 git worktree add -b feat/ask-your-data ..\portfolio-analytics main
 git worktree add -b feat/energypulse ..\portfolio-energy main
 git worktree add -b feat/modernize-studio ..\portfolio-modernize main
```

Abre cada carpeta separada como un proyecto de Codex y pega su prompt. **No uses el mismo working directory para tres agentes que escriben.**

## Revisión / integración

Solo cuando cada agente muestre pruebas y commit:

```powershell
 git switch main
 git merge --no-ff feat/ask-your-data
 git merge --no-ff feat/energypulse
 git merge --no-ff feat/modernize-studio
 node --test tests/*.test.mjs
 python -m http.server 8000
```

Después encarga la tarea de `prompts/04_coordinator.md` (quien trabaja en root `index.html`) y publica con `git add .`, `git commit`, `git push`. En GitHub ve a Settings → Pages → Build and deployment → Deploy from branch → `main` / `(root)`. Visita y verifica el enlace en una ventana privada.

**Si una rama falla, no la mezcles.** Incorpora solo lo que supera pruebas y revisión.

## Cuenta / permisos

El conector GitHub de este chat no tiene permiso de escritura sobre `MariaCM34`. El sitio no se publicará automáticamente desde este chat. Haz el push con tu cuenta o conecta/autorizas una ruta de escritura compatible. No publiques en otra cuenta o Vercel ajeno.
