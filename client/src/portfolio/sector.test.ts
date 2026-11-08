import { describe, expect, it } from 'vitest'
import { en } from '../i18n/en'
import { hi } from '../i18n/hi'
import { ml } from '../i18n/ml'
import { canonicalSectors, SECTORS } from './sector'

describe('canonicalSectors', () => {
  it.each([
    ['Cement and Cement Products', 'Cement & Cement Products'],
    ['It - Software', 'IT - Software'],
    ['Diversified Fmcg', 'Diversified FMCG'],
    ['Agricultural, Commercial and Constr', 'Agricultural, Commercial & Construction Vehicles'],
    ['Commercial Services', 'Commercial Services & Supplies'],
    ['Banks', 'Banks'],
  ])('maps %s to %s', (raw, canonical) => {
    expect(canonicalSectors({ [raw]: 0.5 })).toEqual({ [canonical]: 0.5 })
  })

  it('adds up weights that land on the same sector and keeps unknown sectors as they are', () => {
    expect(canonicalSectors({ 'Textiles and Apparels': 0.1, 'Textiles & Apparels': 0.2, 'Space Tourism': 0.3 })).toEqual({
      'Textiles & Apparels': expect.closeTo(0.3),
      'Space Tourism': 0.3,
    })
  })
})

it('has a name in every language for each sector', () => {
  for (const dictionary of [en, hi, ml]) {
    for (const sector of SECTORS) expect(dictionary).toHaveProperty([`sector.${sector}`])
  }
})
