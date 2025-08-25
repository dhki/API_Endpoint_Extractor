
# ResultWriter makes output file
# if output file is not defined, just write to console
class ResultWriter:
    def __init__(self, path=None):
        self.file = open(path, "w") if path else None
    
    def write(self, url_info: str):
        if self.file:
            self.file.write(url_info + "\n")
        else:
            print(f"[+] {url_info}")
    
    def close(self):
        if self.file:
            self.file.close()