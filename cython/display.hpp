class Display {
public:
  Display();
  Display(const Display&);
  Display& operator=(const Display&);
  ~Display();

private:
  struct DisplayImpl* pimpl;

};
