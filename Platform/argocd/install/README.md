# Instalación de ArgoCD

ArgoCD no se despliega con ArgoCD (problema del "huevo y la gallina"): es el
único componente que se instala manualmente, una sola vez, contra el cluster
`kind`. A partir de ahí, todo lo demás (las apps de `Platform/apps/`) se
gestiona vía GitOps.

Versión fijada: **v3.5.2** (es la que corre hoy en el cluster; actualizar
aquí si se sube de versión, para que el comando siga siendo reproducible).

## Instalación

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.2/manifests/install.yaml
kubectl wait --for=condition=available --timeout=180s deployment -n argocd --all
```

## Bootstrap de las Applications (app of apps)

Una vez que ArgoCD está `Running`, se aplica una única vez el root
`Application` que vive en `Platform/argocd/root-app.yaml`. Ese root apunta a
`Platform/argocd/applications/`, así que de ahí en adelante **agregar o
quitar una app es agregar o quitar un archivo en esa carpeta y hacer push** —
no se vuelve a tocar el cluster a mano.

```bash
kubectl apply -f Platform/argocd/root-app.yaml
```

## Acceder a la UI / CLI (opcional)

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# password inicial:
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```
