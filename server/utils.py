import tkinter

window = tkinter.Tk()
window.title("Chat")
label = tkinter.Label(window,text="hello").pack()
window.geometry('350*200')
window.grid(column=0,row=0)
window.mainloop()