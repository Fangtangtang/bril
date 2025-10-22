
int f(int s[100], int cnt) {
  int another = cnt;
  for (int i = 0; i < cnt; i += 2) {
    s[i] += i;
    another += i;
  }
  return s[0] + another;
}

int g(int s[100], int cnt) {
  int another = cnt;
  for (int i = 0; i < cnt; i += 2) {
    s[i] += i;
    another += i;
    if (cnt > 10) {
      break;
    }
  }
  return s[0] + another;
}

int main() { return 0; }