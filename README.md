## API Endpoint Extractor

### command

**Apk Decompile**

```cmd
python main.py -d --apk_path "apk_path to decompile"
```

- 저장 경로: ./target_smali"



**Extract the permissions of Android Manifest**

Android Manifest 내에서 Permission을 모두 추출하고, permission에 대한 summary와 함께 json 파일로 저장합니다.

```cmd
python main.py -am
```

- permission에 대한 summary는 [공식문서](https://developer.android.com/reference/android/Manifest.permission)에서 제공되는 내용과 동일합니다. 
- 저장 경로: "./outputs/android_manifest_output.json"



