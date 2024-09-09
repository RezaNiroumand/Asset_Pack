from PySide6.QtCore import QObject, Signal
import mmap
import re
import os
import glob
import shutil
import fileinput


class Asset_Pack(QObject):
    progress_changed = Signal(int)
    def __init__(self, main_maya_file_path, copy_destination_folder, project_prefix):
        super().__init__()
        self.maya_file_pattern = r'.mb";|.ma";'
        self.extension_pattern = r'\.tx$|\.tif$|\.png$|\.jpg$|\.exr$|\.mb$|\.ma$|\.abc$|\.ass$|\.vrmesh$|\.wav$|\.WAV$|\.aur$'
        self.tex_ext_list = ('.tif"', '.tx"', '.jpg"', '.png"', '.exr"')

        self.main_maya_file_path = main_maya_file_path

        self.copy_destination_folder = (copy_destination_folder+'/').replace('\\','/')
        self.project_prefix = project_prefix

        self.reports = []
        self.error_reports = []
        self.files_raw_adresses = []
    # -------------------------------------------------------------

    def print_array(self, array, message):
        print(message)
        self.reports.append(message)
        for item in array:
            print(item)
            self.reports.append(item)


    # -------------------------------------------------------------

    def find_addresses_in_line(self, line):
        for part in line.split('"'):
            if re.findall(self.extension_pattern, part):
                return (part)
    
    
    # -------------------------------------------------------------
    
    def find_ref_addresses(self, main_maya_file_path):
        all_maya_files_path = []
        if not os.path.exists(main_maya_file_path):
            print("maya file :" + main_maya_file_path + " not exist!")
            self.error_reports.append("maya file :" + main_maya_file_path + " not exist!")
            return all_maya_files_path
        # read files as binary
        with open(main_maya_file_path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0)
        mm.seek(0)
        file_line = 0
        line = mm.readline()
        file_line +=1
        while line:
            try:
                if line.decode('utf-8').startswith("file -rdi") or line.decode('utf-8').startswith("file -r"):
                    if re.findall(self.maya_file_pattern, line.decode('utf-8')):
                        founded_addresses = self.find_addresses_in_line(line.decode('utf-8')[:-1])
                        print('maya file addresses: ' + founded_addresses)
                        self.reports.append('maya file addresses: ' + founded_addresses)
                        all_maya_files_path.append(founded_addresses)
                        self.files_raw_adresses.append(['maya_files', main_maya_file_path, founded_addresses, file_line])
                        
                    else:
                        line = mm.readline()
                        file_line +=1
                        founded_addresses = self.find_addresses_in_line(line.decode('utf-8')[:-1])
                        print('maya file addresses: ' + founded_addresses)
                        self.reports.append('maya file addresses: ' + founded_addresses)
                        all_maya_files_path.append(founded_addresses)
                        self.files_raw_adresses.append(['maya_files', main_maya_file_path, founded_addresses, file_line])
                line = mm.readline()
                file_line +=1
            except UnicodeDecodeError as e:
                print(e)
                print("skip")
                line = mm.readline()
                file_line +=1
            except Exception as e:
                print(e)
                exit()
        mm.close()
        return all_maya_files_path
    
    
    # -------------------------------------------------------------
    
    def fix_maya_addresses(self, all_maya_files_path):
        # remove repeated files
        all_maya_files_path = list(set(all_maya_files_path))
        # add absolute addresses to relatives
        for i, maya_files_path in enumerate(all_maya_files_path):
            if maya_files_path.startswith("scenes"):
                if 'CAPT' in maya_files_path.split('/')[-1]:
                    all_maya_files_path[i] = "L:/CAPT/LEMONCORE/CAPT_PROJ/" + maya_files_path
                elif 'MMO' in maya_files_path.split('/')[-1]:
                    all_maya_files_path[i] = "T:/dwtv/mmo/Maya_MMO/" + maya_files_path
                elif 'WTP' in maya_files_path.split('/')[-1]:
                    all_maya_files_path[i] = "L:/ODDBOT/WTP/LEMONCORE/WTP_PROJ/" + maya_files_path
                elif 'NQN' in maya_files_path.split('/')[-1]:
                    all_maya_files_path[i] = "T:/dwtv/nqn/Maya_NQN/" + maya_files_path

                # if founded file didn't have a prefix it tries to use the user project prefix

                elif self.project_prefix == 'CAPT':
                    all_maya_files_path[i] = "L:/CAPT/LEMONCORE/CAPT_PROJ/" + maya_files_path
                elif self.project_prefix == 'MMO':
                    all_maya_files_path[i] = "T:/dwtv/mmo/Maya_MMO/" + maya_files_path
                elif self.project_prefix == 'WTP':
                    all_maya_files_path[i] = "L:/ODDBOT/WTP/LEMONCORE/WTP_PROJ/" + maya_files_path
                elif self.project_prefix == 'NQN':
                    all_maya_files_path[i] = "T:/dwtv/nqn/Maya_NQN/" + maya_files_path

                else:
                    print("this reference doesnt have prefix :" + maya_files_path)
                    self.error_reports.append("this reference doesnt have prefix :" + maya_files_path)
            # remove //
            all_maya_files_path[i] = all_maya_files_path[i].replace("//", "/")
        return all_maya_files_path
    
    
    # -------------------------------------------------------------
    # find all files except references
    # -------------------------------------------------------------
    
    def find_addresses(self, maya_file_path):
        
        all_texture_files = []
        all_alembic_files = []
        all_gpu_cache_files = []
        all_aistandin_files = []
        all_vrayproxy_files = []       
        all_audio_files = []
        all_vray_volume_caches = []

        if not os.path.exists(maya_file_path):
            print("maya file :" + maya_file_path + " not exist!")
            self.error_reports.append("maya file :" + maya_file_path + " not exist!")
            return all_texture_files, all_alembic_files, all_gpu_cache_files, all_aistandin_files, all_vrayproxy_files, all_audio_files
        with open(maya_file_path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0)
        mm.seek(0)
        file_line = 0
        line = mm.readline()
        file_line +=1
        while line:
            try:

                if line.decode('utf-8').startswith("file -rdi") or line.decode('utf-8').startswith("file -r"):
                    if re.findall(self.maya_file_pattern, line.decode('utf-8')):
                        founded_addresses = self.find_addresses_in_line(line.decode('utf-8')[:-1])
                        print('maya file addresses: ' + founded_addresses)

                        self.files_raw_adresses.append(['maya_files', maya_file_path, founded_addresses, file_line])
                        
                    else:
                        line = mm.readline()
                        file_line +=1
                        founded_addresses = self.find_addresses_in_line(line.decode('utf-8')[:-1])
                        print('maya file addresses: ' + founded_addresses)

                        self.files_raw_adresses.append(['maya_files', maya_file_path, founded_addresses, file_line])                
                                
                if line.decode('utf-8').startswith('	setAttr "') and any(
                        ext in (line.decode('utf-8')) for ext in self.tex_ext_list):
                    texture_file = self.find_addresses_in_line(line.decode('utf-8'))
                    all_texture_files.append(texture_file)
                    self.files_raw_adresses.append(['texture_files',maya_file_path, texture_file, file_line])
                    print('texture_file_addresses: ' + texture_file)
                    self.reports.append('texture_file_addresses: ' + texture_file)


                if line.decode('utf-8').startswith('	setAttr ".fn') and '.vrmesh"' in line.decode('utf-8'):
                    vrayproxy_file = self.find_addresses_in_line(line.decode('utf-8'))
                    all_vrayproxy_files.append(vrayproxy_file)
                    self.files_raw_adresses.append(['vrayproxy_files',maya_file_path, vrayproxy_file, file_line])
                    print('vrayproxy_file_addresses: ' + vrayproxy_file)
                    self.reports.append('vrayproxy_file_addresses: ' + vrayproxy_file)



                if (line.decode('utf-8').startswith('	setAttr ".ipth"') or line.decode('utf-8').startswith('	setAttr ".ipthr"')) and '.aur"' in line.decode('utf-8'):
                    vray_volume_cache = self.find_addresses_in_line(line.decode('utf-8'))
                    all_vray_volume_caches.append(vray_volume_cache)
                    self.files_raw_adresses.append(['vray_volume_caches',maya_file_path, vray_volume_cache, file_line])
                    print('vray_volume_caches_addresses: ' + vray_volume_cache) 



                if line.decode('utf-8').startswith('	setAttr ".fn') and '.abc"' in line.decode('utf-8'):
                    alembic_file = self.find_addresses_in_line(line.decode('utf-8'))
                    all_alembic_files.append(alembic_file)
                    self.files_raw_adresses.append(['alembic_files', maya_file_path, alembic_file, file_line])
                    print('alembic_file_addresses: ' + alembic_file)
                    self.reports.append('alembic_file_addresses: ' + alembic_file)


                if line.decode('utf-8').startswith('	setAttr ".cfn') and '.abc"' in line.decode('utf-8'):
                    gpu_cache_file = self.find_addresses_in_line(line.decode('utf-8'))
                    all_gpu_cache_files.append(gpu_cache_file)
                    self.files_raw_adresses.append(['GPU_cache_files', maya_file_path, gpu_cache_file, file_line])
                    print('gpu_cache_addresses: ' + gpu_cache_file)
                    self.reports.append('gpu_cache_addresses: ' + gpu_cache_file)


                if line.decode('utf-8').startswith('	setAttr ".dso') and '.ass"' in line.decode('utf-8'):
                    aistandin_file = self.find_addresses_in_line(line.decode('utf-8'))
                    all_aistandin_files.append(aistandin_file)
                    self.files_raw_adresses.append(['aistandin_files', maya_file_path, aistandin_file, file_line])
                    print('aistandin_file_addresses: ' + aistandin_file)
                    self.reports.append('aistandin_file_addresses: ' + aistandin_file)


                if line.decode('utf-8').startswith('	setAttr ".f') and (('.wav"' in line.decode('utf-8')) or ('.WAV"' in line.decode('utf-8'))):
                    audio_file = self.find_addresses_in_line(line.decode('utf-8'))
                    all_audio_files.append(audio_file)
                    self.files_raw_adresses.append(['audio_files', maya_file_path, audio_file, file_line])
                    print('audio_file_addresses: ' + audio_file)
                    self.reports.append('audio_file_addresses: ' + audio_file)


                line = mm.readline()
                file_line +=1
            except UnicodeDecodeError as e:
                print(e)
                print("skip")
                line = mm.readline()
                file_line +=1
            except Exception as e:
                print(e)
                exit()
        mm.close()
        return all_texture_files, all_alembic_files, all_gpu_cache_files, all_aistandin_files, all_vrayproxy_files, all_audio_files, all_vray_volume_caches
    
    
    # -------------------------------------------------------------
    # find udims and sequences and remove repeated texture files
    # -------------------------------------------------------------
    
    
    def fix_texture_addresses_proc(self, all_texture_files):
        # remove repeated files
        all_texture_files = list(set(all_texture_files))
    
        new_texture_files = []
    
        for i, item in enumerate(all_texture_files):
            all_texture_files[i] = all_texture_files[i].replace("//", "/")
            all_texture_files[i] = all_texture_files[i].replace('<udim>', '*')
            all_texture_files[i] = all_texture_files[i].replace('<f>', '*')
        print(all_texture_files)
    
        for i, item in enumerate(all_texture_files):
            # remove extension
            address_no_extension = all_texture_files[i].replace('.' + item.split('.')[-1], '')
            # keep extension
            extension = '.' + item.split('.')[-1]
            # find out if number is in the end of the string
            if (re.search(r"\d+$", address_no_extension)):
                # remove the number in the end of the string and replace with star and add extension
                address_no_extension_no_number = address_no_extension.replace(
                    re.search(r"\d+$", address_no_extension).group(), '')
                all_texture_files[i] = address_no_extension_no_number + '*' + extension
        print(all_texture_files)
    
        i = 0
        while i < len(all_texture_files):
            print(all_texture_files[i])
            if '*' in all_texture_files[i]:
                # print(glob.glob(all_texture_files[i]))
                new_texture_files += glob.glob(all_texture_files[i])
                # remove address with * from list after call globe
                print("delete :" + all_texture_files[i])
                del all_texture_files[i]
                i -= 1
            i += 1
        print(all_texture_files)
        print(new_texture_files)
        for i, new_texture_file in enumerate(new_texture_files):
            new_texture_files[i] = new_texture_files[i].replace("//", "/")
            new_texture_files[i] = new_texture_files[i].replace("\\", "/")
        all_texture_files += new_texture_files
        all_texture_files = list(set(all_texture_files))
        return all_texture_files
    
    
    # -------------------------------------------------------------
    # find textures and scenes in aistandins and add
    # -------------------------------------------------------------
    
    def find_files_in_aistandin(self, aistandin_path):
        print(" s    t   a   n   d   i   n       p   a   t   h   :"+aistandin_path)
        all_aistandin_files = []
        all_aistandin_textures = []
        if not os.path.exists(aistandin_path):
            print("standin file :" + aistandin_path + " not exist!")
            self.error_reports.append("standin file :" + aistandin_path + " does not exist!")
            return all_aistandin_textures, all_aistandin_files
        with open(aistandin_path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0)
        mm.seek(0)
        file_line = 0
        line = mm.readline()
        file_line +=1
        while line:
            if line.decode('utf-8').startswith(' filename "') and '.tx"' in line.decode('utf-8'):
                # print('aistandin texture :' + find_addresses_in_line(line.decode('utf-8')[:-1]))
                founded_addresses =  self.find_addresses_in_line(line.decode('utf-8')[:-1])
                self.reports.append('aistandin texture :' + founded_addresses)
                all_aistandin_textures.append(founded_addresses)
                self.files_raw_adresses.append(['texture_files', aistandin_path, founded_addresses, file_line])
    
            if line.decode('utf-8').startswith(' filename "') and '.ass"' in line.decode('utf-8'):
                # print('aistandin file :' + find_addresses_in_line(line.decode('utf-8')[:-1]))
                founded_addresses =  self.find_addresses_in_line(line.decode('utf-8')[:-1])
                self.reports.append('aistandin file :' + founded_addresses)
                all_aistandin_files.append(founded_addresses)
                self.files_raw_adresses.append(['aistandin_files', aistandin_path, founded_addresses, file_line])
    
            line = mm.readline()
            file_line +=1
        mm.close()
        # print('all_aistandin_textures...............................')
        # print(all_aistandin_textures)
        # print('all_aistandin_files.........................')
        # print(all_aistandin_files)
        return all_aistandin_textures, all_aistandin_files
    
    
    def find_files_in_aistandins(self, all_aistandin_files):
        all_aistandins_textures = []
        all_aistandins_files = []
        print('a    l   l       a   i   s   t   a   n  d    i   n   s       f   i   l   e   s   :')
        print(all_aistandin_files)
        for each_file in all_aistandin_files:
            files = self.find_files_in_aistandin(each_file)
            textures_in_aistandin = files[0]
            files_in_aistandin = files[1]
            print('all_aistandin_textures...............................')
            self.print_array(textures_in_aistandin, "all standins texture files :")
            print('all_aistandin_files.........................')
            self.print_array(files_in_aistandin, "all standins files :")
    
            all_aistandins_textures = all_aistandins_textures + textures_in_aistandin
            all_aistandins_files = all_aistandins_files + files_in_aistandin
        return all_aistandins_textures, all_aistandins_files
    
    
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    
    def maya_file_content_finder(self, all_maya_files_path):
        all_texture_files = []
        all_gpu_cache_files = []
        all_alembic_files = []
        all_aistandin_files = []
        all_vrayproxy_files = []        
        all_audio_files = []
        all_vray_volume_caches = []
    
        for maya_file_path in all_maya_files_path:
            print("finding files in :" + maya_file_path)
            self.reports.append("finding files in :" + maya_file_path)
            all_addreses = self.find_addresses(maya_file_path)
            
            all_texture_files += all_addreses[0]
            all_alembic_files += all_addreses[1]
            all_gpu_cache_files += all_addreses[2]
            all_aistandin_files += all_addreses[3]
            all_vrayproxy_files += all_addreses[4]
            all_audio_files += all_addreses[5]
            all_vray_volume_caches += all_addreses[6]
        return [all_texture_files, all_gpu_cache_files, all_alembic_files, all_aistandin_files, all_vrayproxy_files,
                all_audio_files, all_vray_volume_caches]
    
    
    # -------------------------------------------------------------
    
    def seprate_mb_from_all_maya_files_path(self, all_maya_files_path):
        all_maya_files_path_mb = []
        for i, item in enumerate(all_maya_files_path):
            if item.endswith(".mb"):
                all_maya_files_path_mb.append(item)
                del all_maya_files_path[i]
        return all_maya_files_path, all_maya_files_path_mb
    
    

    # -------------------------------------------------------------
    
    def copy_list(self, address_list, folder):
        if not os.path.exists(self.copy_destination_folder + '/' + folder):
            os.mkdir(self.copy_destination_folder + '/' + folder)
        for address in address_list:
            address = address.replace('\\','/')         
            destination_file = address.split('/')[-1]
            destination_sub_folder = address.split('/')[-2] 

            # print(destination_file)
            # print(destination_sub_folder)
            # print(self.copy_destination_folder)

            if (not os.path.exists(self.copy_destination_folder + folder + '/' +destination_sub_folder+ '/' + destination_file)) and (os.path.exists(address)):
                if not os.path.exists(self.copy_destination_folder + '/' + folder + '/' +destination_sub_folder+'/'.replace('\\','/')):
                    os.makedirs(self.copy_destination_folder + '/' + folder + '/' +destination_sub_folder+'/'.replace('\\','/'))
                shutil.copy(address, self.copy_destination_folder + '/' + folder + '/' +destination_sub_folder+'/'.replace('\\','/'))
            else:
                if (os.path.exists(self.copy_destination_folder + folder + '/' + destination_sub_folder + '/' + destination_file)):
                    print("same file exists in copy destination :" + self.copy_destination_folder + folder + '/' +destination_sub_folder+ '/' + destination_file)
                    self.error_reports.append("same file exists in copy destination :" + self.copy_destination_folder + folder + '/' +destination_sub_folder+ '/' + destination_file)
                if (not os.path.exists(address)):
                    print("source file dose not exists :" + address)
                    self.error_reports.append("source file dose not exists :" + address)
    
    # -------------------------------------------------------------


    def changing_file_address(self, file_address, dependency_addresses_file_type):
        print('dependency_addresses_file_type')
        print(dependency_addresses_file_type)
        print('dependency_addresses_file_type')               
        file_address = file_address.replace('\\','/')
        destination_file = file_address.split('/')[-1]
        #print('>>>>'+file_address)
        destination_sub_folder = file_address.split('/')[-2]        
        
        if file_address.endswith('.ma'):
            file_to_change_address = self.copy_destination_folder+'maya_files/'+ destination_sub_folder + '/' + destination_file
            print('open :'+ file_to_change_address)
      
        elif file_address.endswith('.ass'):
            file_to_change_address = self.copy_destination_folder+ 'aistandin_files/' + destination_sub_folder + '/' + destination_file
            print('open :'+ file_to_change_address) 
   
        else:
            print('unrecognize file to change addresses!') 
            return     
        
        with open(file_to_change_address) as file:
            data = file.readlines() 
        for item in dependency_addresses_file_type:
            print('i t e m')
            print(item)
            destination_sub_folder = item[0].split('/')[-2]
            print('replacing '+item[0]+' with '+ self.copy_destination_folder+item[1]+'/'+destination_sub_folder+'/'+item[0].split('/')[-1] + ' in line>>>>>>>>>>>'+ data[item[2]-1]+'<<<<<<<line>>>'+str(item[2]-1))
            data[item[2]-1]=data[item[2]-1].replace(item[0],self.copy_destination_folder+item[1]+'/'+destination_sub_folder+'/'+item[0].split('/')[-1])

        with open(file_to_change_address, 'w') as file:
            file.writelines( data )

    
    # -------------------------------------------------------------
    
    
    def changing_files_addresses(self):
        for item in self.files_raw_adresses:
            print(item[0]+'----------'+item[1]+'-------------'+item[2]+'-------------'+str(item[3]))
        file_dict = {}
        file_type_file_address_file_line = []
        for file_type, file_name, address , file_line in self.files_raw_adresses:
            if file_name in file_dict:
                file_type_file_address_file_line.append(address)
                file_type_file_address_file_line.append(file_type)
                file_type_file_address_file_line.append(file_line)
                file_dict[file_name].append(file_type_file_address_file_line)
                file_type_file_address_file_line = []
            else:
                file_dict[file_name] = [[address, file_type, file_line]]

        for file_address, dependency_addresses_file_type in file_dict.items():
            self.changing_file_address(file_address, dependency_addresses_file_type)
                   
    
    # -------------------------------------------------------------   
    
    
    def find_all_volume_cache_files(self, all_vray_volume_caches):
        all_vray_volume_caches_files = []
        for item in all_vray_volume_caches:
            directory_path = os.path.dirname(item)        
            all_vray_volume_caches_files += glob.glob(f'{directory_path}/*.aur')
        return all_vray_volume_caches_files

    # -------------------------------------------------------------    

    
    def create_log_file(self):
        with open(self.copy_destination_folder + "log.txt", "a") as file:
            for item in self.reports:
                file.write("%s\n" % item)
            if self.error_reports:
                file.write("errors:\n")
                for item in self.error_reports:
                    file.write("%s\n" % item)
            else:
                file.write("finished without errors.\n")
    
    
    # main ###################################################################
    
    def main(self):

        self.progress_changed.emit(0)
        self.reports.append("\n\n\n"+self.main_maya_file_path+" progress starts...")

        if (not os.path.exists(self.main_maya_file_path)):
            print("you should give main maya file to start.")
            exit()
        all_maya_files_path = self.fix_maya_addresses(self.find_ref_addresses(self.main_maya_file_path))

        # add main file to found referenced file for search
        all_maya_files_path.append(self.main_maya_file_path)
    
        self.print_array(all_maya_files_path, "all referenced maya files :")
        self.progress_changed.emit(10)

        all_maya_files_path, all_maya_files_path_mb = self.seprate_mb_from_all_maya_files_path(all_maya_files_path)
    
        self.print_array(all_maya_files_path_mb, "all referenced maya files mb :")
        self.print_array(all_maya_files_path, "all referenced maya files ma :")


        # -------------------------------------------------------------
    
        all_non_maya_founded_files = self.maya_file_content_finder(all_maya_files_path)
        all_texture_files = all_non_maya_founded_files[0]
        all_gpu_cache_files = all_non_maya_founded_files[1]
        all_alembic_files = all_non_maya_founded_files[2]
        all_aistandins_files_in_main_file = all_non_maya_founded_files[3]
        all_vrayproxy_files = all_non_maya_founded_files[4]
        all_audio_files = all_non_maya_founded_files[5]
        
        all_vray_volume_caches = all_non_maya_founded_files[6]
        all_vray_volume_caches = self.fix_maya_addresses(all_vray_volume_caches)
        all_vray_volume_caches = self.find_all_volume_cache_files(all_vray_volume_caches)
        
        
        
        
        print("start to find standins contents, including textures and nested standins ...")
        self.progress_changed.emit(20)
        self.reports.append("start to find standins contents, including textures and nested standins ...")
    
        overall_aistandins_textures = []
        overall_aistandins_files = all_aistandins_files_in_main_file
        print(overall_aistandins_textures)
        
        
        # run on founded standins for texture and nested standins
        all_aistandins_textures, all_aistandins_files = self.find_files_in_aistandins(overall_aistandins_files)
        all_aistandins_textures = list(set(all_aistandins_textures))
        all_aistandins_files = list(set(all_aistandins_files))
       
        overall_aistandins_textures += all_aistandins_textures
        overall_aistandins_files += all_aistandins_files        
        
        overall_aistandins_files = self.fix_maya_addresses(overall_aistandins_files)
        print('fix overall_aistandins_files')
        print(overall_aistandins_files)       
        
        print('second search standins files:')
        print(all_aistandins_files)
        
        
        
        # run again on founded nested standins for more texture and more nested standins
        if all_aistandins_files:
            all_aistandins_textures, all_aistandins_files = self.find_files_in_aistandins(all_aistandins_files)
            all_aistandins_textures = list(set(all_aistandins_textures))
            all_aistandins_files = list(set(all_aistandins_files))
            overall_aistandins_textures += all_aistandins_textures
            overall_aistandins_files += all_aistandins_files        
        
        all_texture_files += self.fix_maya_addresses(overall_aistandins_textures)
    
        print("finished descovering standins ...")
        self.reports.append("finished descovering standins ...")
    
        self.print_array(all_texture_files, "all_texture_files :")
        self.print_array(all_gpu_cache_files, "all_gpu_cache_files :")
        self.print_array(all_alembic_files, "all_alembic_files :")
        self.print_array(overall_aistandins_textures, "overall_aistandins_textures :")
        self.print_array(all_vrayproxy_files, "all_vrayproxy_files :")
        self.print_array(all_audio_files, "all_vrayproxy_files :")
        
        # print(">>>>>>>>>>>>>>>>>>>>>>>")
        # for item in self.files_raw_adresses:
        #     print(item)
        # print(">>>>>>>>>>>>>>>>>>>>>>>")

        print("finding finished.")
        self.progress_changed.emit(30)
        ######################################################################
    
        self.print_array(all_maya_files_path, "all referenced maya files :")
        self.print_array(all_texture_files, "all_texture_files plus standin texture files :")
    
        print("finding udims and sequences :")
        self.reports.append("finding udims and sequences :")
    
        # find udims and sequences and remove repeated texture files
    
        fix_texture_addresses = self.fix_texture_addresses_proc(self.fix_maya_addresses(all_texture_files))
    
        # sort by name
        fix_texture_addresses.sort()

        # sort by extension
        fix_texture_addresses = sorted(fix_texture_addresses, key=lambda x: x[-3:])
    
        print("fixed_texture_addresses :")
        self.reports.append("fixed_texture_addresses :")
        for i, item in enumerate(fix_texture_addresses):
            print(str(i).zfill(4) + " : " + item)
            self.reports.append(str(i).zfill(4) + " : " + item)
    
        print("start copying...")
        self.reports.append("start copying...")
        self.progress_changed.emit(40)
       
        
        # copy_list make a folder
        self.copy_list(all_maya_files_path, "maya_files")
    
        self.copy_list(all_maya_files_path_mb, "maya_files")
        self.copy_list(all_gpu_cache_files, "GPU_cache_files")
        self.copy_list(all_alembic_files, "alembic_files")
        self.copy_list(overall_aistandins_files, "aistandin_files")
        
        self.copy_list(all_vrayproxy_files, "vrayproxy_files")
        self.copy_list(all_audio_files, "audio_files")


        # copy_list make a folder
        self.copy_list(all_vray_volume_caches, "vray_volume_caches")
        
        
        self.progress_changed.emit(60)
        
        self.copy_list(fix_texture_addresses, "texture_files")

        
        print("finished copying...")
        self.reports.append("finished copying...")

        print("changing addresses...")
        self.reports.append("changing addresses...")
        self.changing_files_addresses()
        
        self.create_log_file()
        self.progress_changed.emit(100)
        # clean seperated log

