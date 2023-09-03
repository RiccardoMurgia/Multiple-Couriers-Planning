; benchmark generated from python API
(set-info :status unknown)
(declare-fun courier_distance_0 () Int)
(declare-fun courier_distance_1 () Int)
(declare-fun u_0_0 () Int)
(declare-fun u_0_1 () Int)
(declare-fun u_0_2 () Int)
(declare-fun u_0_3 () Int)
(declare-fun u_1_0 () Int)
(declare-fun u_1_1 () Int)
(declare-fun u_1_2 () Int)
(declare-fun u_1_3 () Int)
(declare-fun obj () Int)
(declare-fun table_0_3_3 () Bool)
(declare-fun table_0_3_2 () Bool)
(declare-fun table_0_3_1 () Bool)
(declare-fun table_0_3_0 () Bool)
(declare-fun table_0_2_3 () Bool)
(declare-fun table_0_2_2 () Bool)
(declare-fun table_0_2_1 () Bool)
(declare-fun table_0_2_0 () Bool)
(declare-fun table_0_1_3 () Bool)
(declare-fun table_0_1_2 () Bool)
(declare-fun table_0_1_1 () Bool)
(declare-fun table_0_1_0 () Bool)
(declare-fun table_0_0_3 () Bool)
(declare-fun table_0_0_2 () Bool)
(declare-fun table_0_0_1 () Bool)
(declare-fun table_0_0_0 () Bool)
(declare-fun table_1_3_3 () Bool)
(declare-fun table_1_3_2 () Bool)
(declare-fun table_1_3_1 () Bool)
(declare-fun table_1_3_0 () Bool)
(declare-fun table_1_2_3 () Bool)
(declare-fun table_1_2_2 () Bool)
(declare-fun table_1_2_1 () Bool)
(declare-fun table_1_2_0 () Bool)
(declare-fun table_1_1_3 () Bool)
(declare-fun table_1_1_2 () Bool)
(declare-fun table_1_1_1 () Bool)
(declare-fun table_1_1_0 () Bool)
(declare-fun table_1_0_3 () Bool)
(declare-fun table_1_0_2 () Bool)
(declare-fun table_1_0_1 () Bool)
(declare-fun table_1_0_0 () Bool)
(assert
 (>= courier_distance_0 0))
(assert
 (<= courier_distance_0 342))
(assert
 (>= courier_distance_1 0))
(assert
 (<= courier_distance_1 342))
(assert
 (>= u_0_0 0))
(assert
 (<= u_0_0 3))
(assert
 (>= u_0_1 0))
(assert
 (<= u_0_1 3))
(assert
 (>= u_0_2 0))
(assert
 (<= u_0_2 3))
(assert
 (>= u_0_3 0))
(assert
 (<= u_0_3 3))
(assert
 (>= u_1_0 0))
(assert
 (<= u_1_0 3))
(assert
 (>= u_1_1 0))
(assert
 (<= u_1_1 3))
(assert
 (>= u_1_2 0))
(assert
 (<= u_1_2 3))
(assert
 (>= u_1_3 0))
(assert
 (<= u_1_3 3))
(assert
 (<= obj 342))
(assert
 (>= obj 160))
(assert
 (let ((?x363 (ite table_0_3_3 1 0)))
 (let ((?x364 (* ?x363 0)))
 (let ((?x345 (ite table_0_2_2 1 0)))
 (let ((?x346 (* ?x345 0)))
 (let ((?x326 (ite table_0_1_1 1 0)))
 (let ((?x327 (* ?x326 0)))
 (let ((?x309 (ite table_0_0_2 1 0)))
 (let ((?x1265 (* ?x309 86)))
 (let ((?x304 (ite table_0_0_0 1 0)))
 (let ((?x305 (* ?x304 0)))
 (let ((?x15435 (+ ?x305 (* (ite table_0_0_1 1 0) 21) ?x1265 (* (ite table_0_0_3 1 0) 99) (* (ite table_0_1_0 1 0) 21) ?x327 (* (ite table_0_1_2 1 0) 71) (* (ite table_0_1_3 1 0) 80) (* (ite table_0_2_0 1 0) 92) (* (ite table_0_2_1 1 0) 71) ?x346 (* (ite table_0_2_3 1 0) 61) (* (ite table_0_3_0 1 0) 59) (* (ite table_0_3_1 1 0) 80) (* (ite table_0_3_2 1 0) 61) ?x364)))
 (>= obj ?x15435)))))))))))))
(assert
 (let ((?x492 (ite table_1_3_3 1 0)))
 (let ((?x493 (* ?x492 0)))
 (let ((?x474 (ite table_1_2_2 1 0)))
 (let ((?x475 (* ?x474 0)))
 (let ((?x456 (ite table_1_1_1 1 0)))
 (let ((?x457 (* ?x456 0)))
 (let ((?x442 (ite table_1_0_2 1 0)))
 (let ((?x1478 (* ?x442 86)))
 (let ((?x438 (ite table_1_0_0 1 0)))
 (let ((?x439 (* ?x438 0)))
 (let ((?x21124 (+ ?x439 (* (ite table_1_0_1 1 0) 21) ?x1478 (* (ite table_1_0_3 1 0) 99) (* (ite table_1_1_0 1 0) 21) ?x457 (* (ite table_1_1_2 1 0) 71) (* (ite table_1_1_3 1 0) 80) (* (ite table_1_2_0 1 0) 92) (* (ite table_1_2_1 1 0) 71) ?x475 (* (ite table_1_2_3 1 0) 61) (* (ite table_1_3_0 1 0) 59) (* (ite table_1_3_1 1 0) 80) (* (ite table_1_3_2 1 0) 61) ?x493)))
 (>= obj ?x21124)))))))))))))
(assert
 (= table_0_0_0 false))
(assert
 (let ((?x357 (ite table_0_3_0 1 0)))
 (let ((?x341 (ite table_0_2_0 1 0)))
 (let ((?x324 (ite table_0_1_0 1 0)))
 (let ((?x304 (ite table_0_0_0 1 0)))
 (let ((?x311 (ite table_0_0_3 1 0)))
 (let ((?x309 (ite table_0_0_2 1 0)))
 (let ((?x306 (ite table_0_0_1 1 0)))
 (= (+ ?x304 ?x306 ?x309 ?x311) (+ ?x304 ?x324 ?x341 ?x357))))))))))
(assert
 (= (or table_0_0_0 table_0_0_1 table_0_0_2 table_0_0_3) (or table_0_0_0 table_0_1_0 table_0_2_0 table_0_3_0)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_0_0_0 table_0_0_1 table_0_0_2 table_0_0_3) ((_ pbeq 1 1 1 1 1) table_0_0_0 table_0_1_0 table_0_2_0 table_0_3_0)))
(assert
 (= table_0_1_1 false))
(assert
 (let ((?x359 (ite table_0_3_1 1 0)))
 (let ((?x343 (ite table_0_2_1 1 0)))
 (let ((?x326 (ite table_0_1_1 1 0)))
 (let ((?x306 (ite table_0_0_1 1 0)))
 (let ((?x331 (ite table_0_1_3 1 0)))
 (let ((?x328 (ite table_0_1_2 1 0)))
 (let ((?x324 (ite table_0_1_0 1 0)))
 (= (+ ?x324 ?x326 ?x328 ?x331) (+ ?x306 ?x326 ?x343 ?x359))))))))))
(assert
 (= (or table_0_1_0 table_0_1_1 table_0_1_2 table_0_1_3) (or table_0_0_1 table_0_1_1 table_0_2_1 table_0_3_1)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_0_1_0 table_0_1_1 table_0_1_2 table_0_1_3) ((_ pbeq 1 1 1 1 1) table_0_0_1 table_0_1_1 table_0_2_1 table_0_3_1)))
(assert
 (= table_0_2_2 false))
(assert
 (let ((?x361 (ite table_0_3_2 1 0)))
 (let ((?x345 (ite table_0_2_2 1 0)))
 (let ((?x328 (ite table_0_1_2 1 0)))
 (let ((?x309 (ite table_0_0_2 1 0)))
 (let ((?x347 (ite table_0_2_3 1 0)))
 (let ((?x343 (ite table_0_2_1 1 0)))
 (let ((?x341 (ite table_0_2_0 1 0)))
 (= (+ ?x341 ?x343 ?x345 ?x347) (+ ?x309 ?x328 ?x345 ?x361))))))))))
(assert
 (= (or table_0_2_0 table_0_2_1 table_0_2_2 table_0_2_3) (or table_0_0_2 table_0_1_2 table_0_2_2 table_0_3_2)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_0_2_0 table_0_2_1 table_0_2_2 table_0_2_3) ((_ pbeq 1 1 1 1 1) table_0_0_2 table_0_1_2 table_0_2_2 table_0_3_2)))
(assert
 (= table_0_3_3 false))
(assert
 (let ((?x363 (ite table_0_3_3 1 0)))
 (let ((?x347 (ite table_0_2_3 1 0)))
 (let ((?x331 (ite table_0_1_3 1 0)))
 (let ((?x311 (ite table_0_0_3 1 0)))
 (let ((?x361 (ite table_0_3_2 1 0)))
 (let ((?x359 (ite table_0_3_1 1 0)))
 (let ((?x357 (ite table_0_3_0 1 0)))
 (= (+ ?x357 ?x359 ?x361 ?x363) (+ ?x311 ?x331 ?x347 ?x363))))))))))
(assert
 (= (or table_0_3_0 table_0_3_1 table_0_3_2 table_0_3_3) (or table_0_0_3 table_0_1_3 table_0_2_3 table_0_3_3)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_0_3_0 table_0_3_1 table_0_3_2 table_0_3_3) ((_ pbeq 1 1 1 1 1) table_0_0_3 table_0_1_3 table_0_2_3 table_0_3_3)))
(assert
 (= table_1_0_0 false))
(assert
 (let ((?x486 (ite table_1_3_0 1 0)))
 (let ((?x470 (ite table_1_2_0 1 0)))
 (let ((?x454 (ite table_1_1_0 1 0)))
 (let ((?x438 (ite table_1_0_0 1 0)))
 (let ((?x444 (ite table_1_0_3 1 0)))
 (let ((?x442 (ite table_1_0_2 1 0)))
 (let ((?x440 (ite table_1_0_1 1 0)))
 (= (+ ?x438 ?x440 ?x442 ?x444) (+ ?x438 ?x454 ?x470 ?x486))))))))))
(assert
 (= (or table_1_0_0 table_1_0_1 table_1_0_2 table_1_0_3) (or table_1_0_0 table_1_1_0 table_1_2_0 table_1_3_0)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_1_0_0 table_1_0_1 table_1_0_2 table_1_0_3) ((_ pbeq 1 1 1 1 1) table_1_0_0 table_1_1_0 table_1_2_0 table_1_3_0)))
(assert
 (= table_1_1_1 false))
(assert
 (let ((?x488 (ite table_1_3_1 1 0)))
 (let ((?x472 (ite table_1_2_1 1 0)))
 (let ((?x456 (ite table_1_1_1 1 0)))
 (let ((?x440 (ite table_1_0_1 1 0)))
 (let ((?x460 (ite table_1_1_3 1 0)))
 (let ((?x458 (ite table_1_1_2 1 0)))
 (let ((?x454 (ite table_1_1_0 1 0)))
 (= (+ ?x454 ?x456 ?x458 ?x460) (+ ?x440 ?x456 ?x472 ?x488))))))))))
(assert
 (= (or table_1_1_0 table_1_1_1 table_1_1_2 table_1_1_3) (or table_1_0_1 table_1_1_1 table_1_2_1 table_1_3_1)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_1_1_0 table_1_1_1 table_1_1_2 table_1_1_3) ((_ pbeq 1 1 1 1 1) table_1_0_1 table_1_1_1 table_1_2_1 table_1_3_1)))
(assert
 (= table_1_2_2 false))
(assert
 (let ((?x490 (ite table_1_3_2 1 0)))
 (let ((?x474 (ite table_1_2_2 1 0)))
 (let ((?x458 (ite table_1_1_2 1 0)))
 (let ((?x442 (ite table_1_0_2 1 0)))
 (let ((?x476 (ite table_1_2_3 1 0)))
 (let ((?x472 (ite table_1_2_1 1 0)))
 (let ((?x470 (ite table_1_2_0 1 0)))
 (= (+ ?x470 ?x472 ?x474 ?x476) (+ ?x442 ?x458 ?x474 ?x490))))))))))
(assert
 (= (or table_1_2_0 table_1_2_1 table_1_2_2 table_1_2_3) (or table_1_0_2 table_1_1_2 table_1_2_2 table_1_3_2)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_1_2_0 table_1_2_1 table_1_2_2 table_1_2_3) ((_ pbeq 1 1 1 1 1) table_1_0_2 table_1_1_2 table_1_2_2 table_1_3_2)))
(assert
 (= table_1_3_3 false))
(assert
 (let ((?x492 (ite table_1_3_3 1 0)))
 (let ((?x476 (ite table_1_2_3 1 0)))
 (let ((?x460 (ite table_1_1_3 1 0)))
 (let ((?x444 (ite table_1_0_3 1 0)))
 (let ((?x490 (ite table_1_3_2 1 0)))
 (let ((?x488 (ite table_1_3_1 1 0)))
 (let ((?x486 (ite table_1_3_0 1 0)))
 (= (+ ?x486 ?x488 ?x490 ?x492) (+ ?x444 ?x460 ?x476 ?x492))))))))))
(assert
 (= (or table_1_3_0 table_1_3_1 table_1_3_2 table_1_3_3) (or table_1_0_3 table_1_1_3 table_1_2_3 table_1_3_3)))
(assert
 (= ((_ pbeq 1 1 1 1 1) table_1_3_0 table_1_3_1 table_1_3_2 table_1_3_3) ((_ pbeq 1 1 1 1 1) table_1_0_3 table_1_1_3 table_1_2_3 table_1_3_3)))
(assert
 ((_ pbeq 1 1 1 1 1 1 1 1 1) table_0_0_0 table_0_1_0 table_0_2_0 table_0_3_0 table_1_0_0 table_1_1_0 table_1_2_0 table_1_3_0))
(assert
 ((_ pbeq 1 1 1 1 1 1 1 1 1) table_0_0_0 table_0_0_1 table_0_0_2 table_0_0_3 table_1_0_0 table_1_0_1 table_1_0_2 table_1_0_3))
(assert
 ((_ pbeq 1 1 1 1 1 1 1 1 1) table_0_0_1 table_0_1_1 table_0_2_1 table_0_3_1 table_1_0_1 table_1_1_1 table_1_2_1 table_1_3_1))
(assert
 ((_ pbeq 1 1 1 1 1 1 1 1 1) table_0_1_0 table_0_1_1 table_0_1_2 table_0_1_3 table_1_1_0 table_1_1_1 table_1_1_2 table_1_1_3))
(assert
 ((_ pbeq 1 1 1 1 1 1 1 1 1) table_0_0_2 table_0_1_2 table_0_2_2 table_0_3_2 table_1_0_2 table_1_1_2 table_1_2_2 table_1_3_2))
(assert
 ((_ pbeq 1 1 1 1 1 1 1 1 1) table_0_2_0 table_0_2_1 table_0_2_2 table_0_2_3 table_1_2_0 table_1_2_1 table_1_2_2 table_1_2_3))
(assert
 ((_ pble 18 20 17 6 20 17 6 20 17 6 20 17 6) table_0_0_0 table_0_0_1 table_0_0_2 table_0_1_0 table_0_1_1 table_0_1_2 table_0_2_0 table_0_2_1 table_0_2_2 table_0_3_0 table_0_3_1 table_0_3_2))
(assert
 (let ((?x361 (ite table_0_3_2 1 0)))
 (let ((?x359 (ite table_0_3_1 1 0)))
 (let ((?x357 (ite table_0_3_0 1 0)))
 (= (+ ?x357 ?x359 ?x361) 1)))))
(assert
 (let ((?x347 (ite table_0_2_3 1 0)))
 (let ((?x331 (ite table_0_1_3 1 0)))
 (let ((?x311 (ite table_0_0_3 1 0)))
 (= (+ ?x311 ?x331 ?x347) 1)))))
(assert
 (let ((?x361 (ite table_0_3_2 1 0)))
 (let ((?x359 (ite table_0_3_1 1 0)))
 (let ((?x357 (ite table_0_3_0 1 0)))
 (let ((?x345 (ite table_0_2_2 1 0)))
 (let ((?x343 (ite table_0_2_1 1 0)))
 (let ((?x341 (ite table_0_2_0 1 0)))
 (let ((?x328 (ite table_0_1_2 1 0)))
 (let ((?x326 (ite table_0_1_1 1 0)))
 (let ((?x324 (ite table_0_1_0 1 0)))
 (let ((?x309 (ite table_0_0_2 1 0)))
 (let ((?x306 (ite table_0_0_1 1 0)))
 (let ((?x304 (ite table_0_0_0 1 0)))
 (let ((?x21269 (+ ?x304 ?x306 ?x309 ?x324 ?x326 ?x328 ?x341 ?x343 ?x345 ?x357 ?x359 ?x361)))
 (>= ?x21269 1)))))))))))))))
(assert
 (let ((?x361 (ite table_0_3_2 1 0)))
 (let ((?x359 (ite table_0_3_1 1 0)))
 (let ((?x357 (ite table_0_3_0 1 0)))
 (let ((?x345 (ite table_0_2_2 1 0)))
 (let ((?x343 (ite table_0_2_1 1 0)))
 (let ((?x341 (ite table_0_2_0 1 0)))
 (let ((?x328 (ite table_0_1_2 1 0)))
 (let ((?x326 (ite table_0_1_1 1 0)))
 (let ((?x324 (ite table_0_1_0 1 0)))
 (let ((?x309 (ite table_0_0_2 1 0)))
 (let ((?x306 (ite table_0_0_1 1 0)))
 (let ((?x304 (ite table_0_0_0 1 0)))
 (let ((?x21269 (+ ?x304 ?x306 ?x309 ?x324 ?x326 ?x328 ?x341 ?x343 ?x345 ?x357 ?x359 ?x361)))
 (<= ?x21269 342)))))))))))))))
(assert
 ((_ pble 30 20 17 6 20 17 6 20 17 6 20 17 6) table_1_0_0 table_1_0_1 table_1_0_2 table_1_1_0 table_1_1_1 table_1_1_2 table_1_2_0 table_1_2_1 table_1_2_2 table_1_3_0 table_1_3_1 table_1_3_2))
(assert
 (let ((?x490 (ite table_1_3_2 1 0)))
 (let ((?x488 (ite table_1_3_1 1 0)))
 (let ((?x486 (ite table_1_3_0 1 0)))
 (= (+ ?x486 ?x488 ?x490) 1)))))
(assert
 (let ((?x476 (ite table_1_2_3 1 0)))
 (let ((?x460 (ite table_1_1_3 1 0)))
 (let ((?x444 (ite table_1_0_3 1 0)))
 (= (+ ?x444 ?x460 ?x476) 1)))))
(assert
 (let ((?x490 (ite table_1_3_2 1 0)))
 (let ((?x488 (ite table_1_3_1 1 0)))
 (let ((?x486 (ite table_1_3_0 1 0)))
 (let ((?x474 (ite table_1_2_2 1 0)))
 (let ((?x472 (ite table_1_2_1 1 0)))
 (let ((?x470 (ite table_1_2_0 1 0)))
 (let ((?x458 (ite table_1_1_2 1 0)))
 (let ((?x456 (ite table_1_1_1 1 0)))
 (let ((?x454 (ite table_1_1_0 1 0)))
 (let ((?x442 (ite table_1_0_2 1 0)))
 (let ((?x440 (ite table_1_0_1 1 0)))
 (let ((?x438 (ite table_1_0_0 1 0)))
 (let ((?x25748 (+ ?x438 ?x440 ?x442 ?x454 ?x456 ?x458 ?x470 ?x472 ?x474 ?x486 ?x488 ?x490)))
 (>= ?x25748 1)))))))))))))))
(assert
 (let ((?x490 (ite table_1_3_2 1 0)))
 (let ((?x488 (ite table_1_3_1 1 0)))
 (let ((?x486 (ite table_1_3_0 1 0)))
 (let ((?x474 (ite table_1_2_2 1 0)))
 (let ((?x472 (ite table_1_2_1 1 0)))
 (let ((?x470 (ite table_1_2_0 1 0)))
 (let ((?x458 (ite table_1_1_2 1 0)))
 (let ((?x456 (ite table_1_1_1 1 0)))
 (let ((?x454 (ite table_1_1_0 1 0)))
 (let ((?x442 (ite table_1_0_2 1 0)))
 (let ((?x440 (ite table_1_0_1 1 0)))
 (let ((?x438 (ite table_1_0_0 1 0)))
 (let ((?x25748 (+ ?x438 ?x440 ?x442 ?x454 ?x456 ?x458 ?x470 ?x472 ?x474 ?x486 ?x488 ?x490)))
 (<= ?x25748 342)))))))))))))))
(assert
 (not (and table_0_0_1 table_0_1_0)))
(assert
 (let ((?x1701 (+ u_0_0 1)))
 (>= u_0_1 (- ?x1701 (* 4 (- 1 (ite table_0_0_1 1 0)))))))
(assert
 (not (and table_0_0_2 table_0_2_0)))
(assert
 (let ((?x1701 (+ u_0_0 1)))
 (>= u_0_2 (- ?x1701 (* 4 (- 1 (ite table_0_0_2 1 0)))))))
(assert
 (not (and table_0_1_0 table_0_0_1)))
(assert
 (let ((?x1838 (+ u_0_1 1)))
 (>= u_0_0 (- ?x1838 (* 4 (- 1 (ite table_0_1_0 1 0)))))))
(assert
 (not (and table_0_1_2 table_0_2_1)))
(assert
 (let ((?x1838 (+ u_0_1 1)))
 (>= u_0_2 (- ?x1838 (* 4 (- 1 (ite table_0_1_2 1 0)))))))
(assert
 (not (and table_0_2_0 table_0_0_2)))
(assert
 (let ((?x1960 (+ u_0_2 1)))
 (>= u_0_0 (- ?x1960 (* 4 (- 1 (ite table_0_2_0 1 0)))))))
(assert
 (not (and table_0_2_1 table_0_1_2)))
(assert
 (let ((?x1960 (+ u_0_2 1)))
 (>= u_0_1 (- ?x1960 (* 4 (- 1 (ite table_0_2_1 1 0)))))))
(assert
 (not (and table_1_0_1 table_1_1_0)))
(assert
 (let ((?x2570 (+ u_1_0 1)))
 (>= u_1_1 (- ?x2570 (* 4 (- 1 (ite table_1_0_1 1 0)))))))
(assert
 (not (and table_1_0_2 table_1_2_0)))
(assert
 (let ((?x2570 (+ u_1_0 1)))
 (>= u_1_2 (- ?x2570 (* 4 (- 1 (ite table_1_0_2 1 0)))))))
(assert
 (not (and table_1_1_0 table_1_0_1)))
(assert
 (let ((?x2704 (+ u_1_1 1)))
 (>= u_1_0 (- ?x2704 (* 4 (- 1 (ite table_1_1_0 1 0)))))))
(assert
 (not (and table_1_1_2 table_1_2_1)))
(assert
 (let ((?x2704 (+ u_1_1 1)))
 (>= u_1_2 (- ?x2704 (* 4 (- 1 (ite table_1_1_2 1 0)))))))
(assert
 (not (and table_1_2_0 table_1_0_2)))
(assert
 (let ((?x2826 (+ u_1_2 1)))
 (>= u_1_0 (- ?x2826 (* 4 (- 1 (ite table_1_2_0 1 0)))))))
(assert
 (not (and table_1_2_1 table_1_1_2)))
(assert
 (let ((?x2826 (+ u_1_2 1)))
 (>= u_1_1 (- ?x2826 (* 4 (- 1 (ite table_1_2_1 1 0)))))))
(check-sat)
