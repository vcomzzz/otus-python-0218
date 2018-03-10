#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertoolsю
# Можно свободно определять свои функции и т.п.
# -----------------

from itertools import groupby, combinations, product
import sys


class Cards:
    ranks = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}

    @classmethod
    def rank(cls, card):
        return cls.ranks[card[0]]

    @classmethod
    def joker(cls, color):
        if color == '?B':
            sp = ['C', 'S']
        elif color == '?R':
            sp = ['H', 'D']
        else:
            sys.exit('Unknow suite: '+color)
        for r, s in product(cls.ranks.keys(), sp):
            yield r + s



def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему"""
    return sorted([Cards.rank(c[0]) for c in hand], reverse=True)


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    for c1, c2 in zip(hand[1:], hand):
        if c1[1] != c2[1]:
            return False
    return True


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""
    for r2, r1 in zip(ranks[1:], ranks):
        if not r1 == r2 + 1:
            return False
    return True


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""
    for k, g in groupby(ranks):
        if(len(list(g)) == n):
            return k
    return None


def two_pair(ranks):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None"""
    p = []
    for k, g in groupby(ranks):
        if len(list(g)) == 2:
            p.append(k)
    if len(p) == 2:
        return tuple(p)
    else:
        return None


def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    return list(max(combinations(hand, 5), key=lambda x: hand_rank(x)))


def joker_hand(h, j):
    """Все варианты из набора карт и одного джокерa"""
    for cj in Cards.joker(j):
        if cj not in h:
            for hand in combinations(h + [cj], 5):
                yield hand


def joker2_hand(h, j1, j2):
    """Все варианты из набора карт и двух джокеров"""
    for cj1, cj2 in product(Cards.joker(j1), Cards.joker(j2)):
        if cj1 not in h and cj2 not in h:
            for hand in combinations(h + [cj1] + [cj2], 5):
                yield hand


def best_wild_hand(hand):
    """best_hand но с джокерами"""
    hj = []
    hw = []
    for c in hand:
        if c[0] == '?':
            hj.append(c)
        else:
            hw.append(c)

    if len(hj) == 0:
        return best_hand(hand)
    elif len(hj) == 1:
        return list(max(joker_hand(hw, hj[0]), key=lambda x: hand_rank(x)))
    elif len(hj) == 2:
        return list(max(joker2_hand(hw, hj[0], hj[1]), key=lambda x: hand_rank(x)))


def test_best_hand():
    print("test_best_hand...")
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


def test_best_wild_hand():
    print("test_best_wild_hand...")
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')

if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
