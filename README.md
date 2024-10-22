# Redis Analyzer

To run in the cluster, first set up kubectl:

* For [dev](https://dev2.k8s-login.notartificial.xyz/)
* For [prod](https://prod2.k8s-login.notartificial.xyz/)

Then check if the deployment is already active:

```
kubectl get deployments -n charles-experiment
```

To deploy if not:

```
kubectl apply -f k8s_python.yaml
```

To run the script in the pod:

```
kubectl get pods -l app=python-dev -n charles-experiment
```

Note the pod name from the above

```
POD_NAME=$(kubectl get pods -l app=python-dev -n charles-experiment -o name | cut -d'/' -f2)
kubectl cp ./mem_usage.py "$POD_NAME:/root/mem_usage.py" -n charles-experiment

# Namespace here is the alab namespace you want to get info on
kubectl exec -it "$POD_NAME" -n charles-experiment -- python /root/mem_usage.py redis://redis-read-tunnel.<namespace>.svc.cluster.local
```

To get a prompt into the pod, do:

```
POD_NAME=$(kubectl get pods -l app=python-dev -n charles-experiment -o name | cut -d'/' -f2)
kubectl exec -it "$POD_NAME" -n charles-experiment -- /bin/bash
```
