当前桶下有两个一级目录（前缀）：

- `highlighted_image/`

- `original_image/`

Example Code:
```
# pip install boto3
import boto3

session = boto3.session.Session()
s3 = session.client(
    "s3",
    region_name="auto",
    endpoint_url="https://288ea43a167a7fc2d608ba1a68b16d29.r2.cloudflarestorage.com",
    aws_access_key_id="AKIA_xxx",
    aws_secret_access_key="SECRET_xxx",
)

s3.put_object(Bucket="ch-technica", Key="hello.txt", Body=b"Hello R2", ContentType="text/plain")
```

遵循基本的AWS SDK