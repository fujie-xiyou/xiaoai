import os
from tools.text import texts1
from 卢本伟.texts2 import texts as texts_lu

# 你的wav文件所在的目录
work_dir = "/Users/fujie/Downloads/lu"
os.chdir(work_dir)

# 小爱同学的 Authorization(抓包获取)
Authorization = "DO-TOKEN-V1 app_id:326813440150602752,scope_data:eyJkIjoiYjljZjkyZWVjMDNlYmJjMyJ9,access_token:V3_zO12DXKMsm7JPEHPcpiGVll62hN5F_4Ja1C4lKxZP3AEC-h5p1SFGQHMqGthtA7GVuQB_SzyAbJPmXFrdFmAQJS3hdWNKhmnnn82eOPaPW9I032mvhH--_B0zDcOAhmGif97K3aR7ecgYsRE75aYHa8Hxunaw1GeQJipG0DeVQs"
# 提交的时候用的音色名称
name = "模仿卢本伟"

# 性别(男：male，女：female)
sex = "male"

texts = texts_lu

n = len(texts) + 1

src_file_type = "wav"
