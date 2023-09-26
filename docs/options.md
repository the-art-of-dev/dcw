# Options


## Service

```yaml
web-app:
  image: nginx:latest
  ports:
   - 8080:80
  environment:
    secret_key: blabla
  labels:
    dcw.service_groups: qa
```


## Environment

Example 1
```env
dcw.service_groups=infra,qa
dcw.tenant=ep
dcw
```

Example 2
```
dcw.services=web-app
dcw.tenant=local
```

## Deployment specification

