# aimlfw-tensorboard

### Installation

```bash
git clone https://github.com/sodyn99/aimlfw-tensorboard.git Tensorboard
```

### Usage

```bash
cd Tensorboard
```
```bash
./deploy.sh
```

*Please Wait*<br>Logs:

```bash
kubectl logs tensorboard-dashboard -n traininghost -f
```

### Port-Forwarding

```bash
./port-forward.sh
```

### Access Tensorboard

[http://localhost:32108](http://localhost:32108)
