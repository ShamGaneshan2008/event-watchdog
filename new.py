# First Task
class User:
    def get_name(self):
        return self.name.upper()
    def age(self, current_year):
        age = current_year - self.birthyear
        return age
    def __init__(self, name, birthyear):
        self.name = name
        self.birthyear = birthyear

name = User("John", 1999)
print(name.age(2023))
print(name.get_name())

