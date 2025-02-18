class Base:
    # def __init_subclass__(cls, **kwargs):
    #     print(cls)

    def __init__(self):
        print("base")


# class New(Base):
#     def __init__(self):
#         super().__init__()
#         print("new")
#
#     pass

# new = New()