import mouse
import random
import matplotlib.pyplot as plt
import numpy

def random_pt():
    return numpy.array([random.uniform(0, 1920), random.uniform(0, 1080)])

def main():
    _, ax = plt.subplots()
    #xs = []
    #ys = []
    #cs = []
    for _ in range(100):
        xs = []
        ys = []
        cs = []
        bc = mouse.bezier_builder(random_pt(), random_pt())
        #for cp in bc.control_points:
        #    xs.append(cp[0])
        #    ys.append(cp[1])
        #    cs.append(2)
        mm = mouse.MouseMover(bc)
        while not mm.done():
            mm.advance_t()
            pt = mm.bezier_curve.eval(mm.t)
            xs.append(pt[0])
            ys.append(pt[1])
            cs.append(mm.t)
        ax.plot(xs, ys)
    #ax.scatter(xs, ys, c=cs)
    plt.show()

if __name__ == "__main__":
    main()