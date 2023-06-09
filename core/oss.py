
import re
from typing import List, Union

from fastapi import UploadFile


class ObjectError(Exception):
    def __init__(self, object: str):
        self.object = object


class ObjectNotFoundError(ObjectError):
    pass


class ObjectConflictError(ObjectError):
    pass


async def getObjectStream(
    oss: any,
    path: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    pathList = [
        item for item in re.split(r"[/|\\]+", path) if item != ""
    ]
    filename = pathList[-1]
    path = "/".join([area, str(user_id)] + pathList)

    resp = await oss.list_objects_v2(
        Bucket=bucket,
        Prefix=path,
    )
    c = resp.get("Contents", [])

    if path not in [item["Key"] for item in c]:
        raise ObjectNotFoundError(path)

    resp = await oss.get_object(
        Bucket=bucket,
        Key=path
    )

    return filename, resp["Body"]


async def getObjectList(
    oss: any,
    path: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    pathList = [
        item for item in re.split(r"[/|\\]+", path) if item != ""
    ]
    prefix = "/".join([area, str(user_id)] + pathList) + "/"

    resp = await oss.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
        Delimiter="/"
    )

    if cp := resp.get("CommonPrefixes"):
        dirs = [{
            "name": item["Prefix"].split("/")[-2],
            "type": "folder",
            "modified_time": 0,
            "src": "",
            "size": 0
        } for item in cp]
    else:
        dirs = []

    if c := resp.get("Contents"):
        files = [{
            "name": item["Key"].split("/")[-1],
            "type": "file",
            "modified_time": int(item["LastModified"].timestamp()),
            "src": f"{'/'.join(pathList)}/" + item["Key"].split("/")[-1],
            "size": item["Size"]
        } for item in c if item["Key"].split("/")[-1] != "__dir__"]
    else:
        files = []

    return dirs + files


async def deleteObjects(
    oss: any,
    names: List[str],
    path: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    pathList = [item for item in re.split(r"[/|\\]+", path) if item != ""]

    objects = []
    for name in names:
        pathPrefix = "/".join([area, str(user_id)] + pathList + [name])
        resp = await oss.list_objects_v2(
            Bucket=bucket,
            Prefix=pathPrefix,
        )
        c = resp.get("Contents", [])
        if pathPrefix in [item["Key"] for item in c]:
            objects.append({"Key": pathPrefix})
        else:
            cd = [
                item for item in c
                if item["Key"].startswith(f"{pathPrefix}/")
            ]
            if len(cd) == 0:
                raise ObjectNotFoundError(pathPrefix)
            objects.extend(cd)

    await oss.delete_objects(
        Bucket=bucket,
        Delete={
            "Objects": objects
        }
    )


async def putObjects(
    oss: any,
    files: List[UploadFile],
    dst: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    dstList = [item for item in re.split(r"[/|\\]+", dst) if item != ""]

    for file in files:
        fileKey = "/".join([area, str(user_id)] + dstList + [file.filename])
        resp = await oss.list_objects_v2(
            Bucket=bucket,
            Prefix=fileKey,
        )
        c = resp.get("Content", [])
        if fileKey in [item["Key"] for item in c]:
            raise ObjectConflictError(fileKey)
        else:
            cd = [
                item for item in c
                if item["Key"].startswith(f"{fileKey}/")
            ]
            if len(cd) != 0:
                raise ObjectConflictError(f"{fileKey}/")
        await oss.upload_fileobj(
            file,
            bucket,
            fileKey
        )


async def _transferObjects(
    oss: any,
    bucket: str,
    srcKey: str,
    sc: list,
    dstKey: str,
    dc: list,
    action: str
):
    # 判断目标文件是否存在
    if dstKey in [item["Key"] for item in dc]:  # 目标文件存在
        raise ObjectConflictError(dstKey)
    else:
        dcd = [
            item for item in dc
            if item["Key"].startswith(f"{dstKey}/")
        ]
        if len(dcd) != 0:  # 目标文件夹存在
            raise ObjectConflictError(f"{dstKey}/")

    # 判断源文件是否存在
    if srcKey in [item["Key"] for item in sc]:  # 源文件存在
        await oss.copy_object(
            Bucket=bucket,
            Key=dstKey,
            CopySource={
                "Bucket": bucket,
                "Key": srcKey
            }
        )
        if action == "move":
            await oss.delete_object(
                Bucket=bucket,
                Key=srcKey
            )
    else:
        scd = [
            item for item in sc
            if item["Key"].startswith(f"{srcKey}/")
        ]
        if len(scd) == 0:  # 源文件夹不存在
            raise ObjectNotFoundError(srcKey)

        # 源文件夹存在
        for key in [item["Key"] for item in scd]:
            await oss.copy_object(
                Bucket=bucket,
                Key=key.replace(f"{srcKey}/", f"{dstKey}/"),
                CopySource={
                    "Bucket": bucket,
                    "Key": key
                }
            )
            if action == "move":
                await oss.delete_object(
                    Bucket=bucket,
                    Key=key
                )


async def moveObjects(
    oss: any,
    names: List[str],
    src_path: str,
    dst_path: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    srcPathList = [
        item for item in re.split(r"[/|\\]+", src_path) if item != ""
    ]
    dstPathList = [
        item for item in re.split(r"[/|\\]+", dst_path) if item != ""
    ]
    srcPathPrefix = "/".join([area, str(user_id)] + srcPathList)
    dstPathPrefix = "/".join([area, str(user_id)] + dstPathList)

    for name in names:
        srcKey = f"{srcPathPrefix}/{name}"
        dstKey = f"{dstPathPrefix}/{name}"
        srcResp = await oss.list_objects_v2(
            Bucket=bucket,
            Prefix=srcKey,
        )
        destResp = await oss.list_objects_v2(
            Bucket=bucket,
            Prefix=dstKey
        )
        sc = srcResp.get("Contents", [])
        dc = destResp.get("Contents", [])

        await _transferObjects(oss, bucket, srcKey, sc, dstKey, dc, "move")


async def copyObjects(
    oss: any,
    names: List[str],
    src_path: str,
    dst_path: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    srcPathList = [
        item for item in re.split(r"[/|\\]+", src_path) if item != ""
    ]
    dstPathList = [
        item for item in re.split(r"[/|\\]+", dst_path) if item != ""
    ]
    srcPathPrefix = "/".join([area, str(user_id)] + srcPathList)
    dstPathPrefix = "/".join([area, str(user_id)] + dstPathList)

    for name in names:
        srcKey = f"{srcPathPrefix}/{name}"
        dstKey = f"{dstPathPrefix}/{name}"
        srcResp = await oss.list_objects_v2(
            Bucket=bucket,
            Prefix=srcKey,
        )
        destResp = await oss.list_objects_v2(
            Bucket=bucket,
            Prefix=dstKey
        )
        sc = srcResp.get("Contents", [])
        dc = destResp.get("Contents", [])

        await _transferObjects(oss, bucket, srcKey, sc, dstKey, dc, "copy")


async def renameObject(
    oss: any,
    path: str,
    old_name: str,
    new_name: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    pathList = [item for item in re.split(r"[/|\\]+", path) if item != ""]
    pathPrefix = "/".join([area, str(user_id)] + pathList)

    srcKey = f"{pathPrefix}/{old_name}"
    dstKey = f"{pathPrefix}/{new_name}"
    srcResp = await oss.list_objects_v2(
        Bucket=bucket,
        Prefix=srcKey,
    )
    destResp = await oss.list_objects_v2(
        Bucket=bucket,
        Prefix=dstKey
    )
    sc = srcResp.get("Contents", [])
    dc = destResp.get("Contents", [])

    await _transferObjects(oss, bucket, srcKey, sc, dstKey, dc, "move")


async def getShareFilePathAndType(
    oss: any,
    path: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    pathList = [
        item for item in re.split(r"[/|\\]+", path) if item != ""
    ]
    path = "/".join([area, str(user_id)] + pathList)

    resp = await oss.list_objects_v2(
        Bucket=bucket,
        Prefix=path,
    )
    c = resp.get("Contents", [])
    if len(c) == 0:
        raise FileNotFoundError(path)
    if path in [item["Key"] for item in c]:
        return path, "file"
    else:
        c = [
            item for item in c
            if item["Key"].startswith(f"{path}/")
        ]
        if len(c) == 0:
            raise FileNotFoundError(f"{path}/")
        return path, "folder"


async def recvShareFile(
    oss: any,
    src_path: str,
    name: str,
    dst_path: str,
    bucket: str,
    area: str,
    user_id: Union[str, int]
):
    dstPathList = [
        item for item in re.split(r"[/|\\]+", dst_path) if item != ""
    ]
    dst_path = "/".join([area, str(user_id)] + dstPathList + [name])

    srcResp = await oss.list_objects_v2(
        Bucket=bucket,
        Prefix=src_path,
    )
    destResp = await oss.list_objects_v2(
        Bucket=bucket,
        Prefix=dst_path
    )
    sc = srcResp.get("Contents", [])
    dc = destResp.get("Contents", [])

    await _transferObjects(oss, bucket, src_path, sc, dst_path, dc, "copy")
