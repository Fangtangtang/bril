def main():
    a = 10000
    b = 0
    c = 2800
    d = 0
    e = 0
    f = [0] * (2801)
    g = 0

    while b - c != 0:
        f[b] = a // 5
        b += 1

    while True:
        e = d % a
        d = 0
        g = c * 2
        if g == 0:
            break
        b = c
        while True:
            d = d + f[b] * a
            g -= 1
            f[b] = d % g
            d //= g
            g -= 1
            b -= 1
            if b == 0:
                break
            d *= b
        c -= 14
        print(str(e + d // a), end="")

if __name__ == "__main__":
    main()
