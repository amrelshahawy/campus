import pandas as pd
from xlrd import XLRDError
import pyomo.core as pyomo
from .modelhelper import *


def read_excel(filename):
    """Read Excel input file and prepare URBS input dict.

    Reads an Excel spreadsheet that adheres to the structure shown in
    mimo-example.xlsx. Two preprocessing steps happen here:
    1. Column titles in 'Demand' and 'SupIm' are split, so that
    'Site.Commodity' becomes the MultiIndex column ('Site', 'Commodity').
    2. The attribute 'annuity-factor' is derived here from the columns 'wacc'
    and 'depreciation' for 'Process', 'Transmission' and 'Storage'.

    Args:
        filename: filename to an Excel spreadsheet with the required sheets
            'Commodity', 'Process', 'Transmission', 'Storage', 'Demand' and
            'SupIm'.

    Returns:
        a dict of 6 DataFrames

    Example:
        >>> data = read_excel('mimo-example.xlsx')
        >>> data['global_prop'].loc['CO2 limit', 'value']
        150000000
    """
    with pd.ExcelFile(filename) as xls:

        sheetnames = xls.sheet_names

        site = xls.parse('Site').set_index(['Name'])
        commodity = (
            xls.parse('Commodity').set_index(['Site', 'Commodity', 'Type']))
        process = xls.parse('Process').set_index(['Site', 'Process'])
        process_commodity = (
            xls.parse('Process-Commodity')
               .set_index(['Process', 'Commodity', 'Direction']))
        transmission = (
            xls.parse('Transmission')
               .set_index(['Site In', 'Site Out',
                           'Transmission', 'Commodity']))
        storage = (
            xls.parse('Storage').set_index(['Site', 'Storage', 'Commodity']))
        demand = xls.parse('Demand').set_index(['t'])
        supim = xls.parse('SupIm').set_index(['t'])
        buy_sell_price = xls.parse('Buy-Sell-Price').set_index(['t'])
        dsm = xls.parse('DSM').set_index(['Site', 'Commodity'])
        if 'Global' in sheetnames:
            global_prop = xls.parse('Global').set_index(['Property'])
        else:
            raise KeyError('Rename worksheet "Hacks" to "Global" and the ' +
                           'line "Global CO2 limit" into "CO2 limit"!')
        if 'TimeVarEff' in sheetnames:
            eff_factor = (xls.parse('TimeVarEff')
                          .set_index(['t']))

            eff_factor.columns = split_columns(eff_factor.columns, '.')
        else:
            eff_factor = pd.DataFrame()

    # prepare input data
    # split columns by dots '.', so that 'DE.Elec' becomes the two-level
    # column index ('DE', 'Elec')
    demand.columns = split_columns(demand.columns, '.')
    supim.columns = split_columns(supim.columns, '.')
    buy_sell_price.columns = split_columns(buy_sell_price.columns, '.')

    data = {
        'global_prop': global_prop,
        'site': site,
        'commodity': commodity,
        'process': process,
        'process_commodity': process_commodity,
        'transmission': transmission,
        'storage': storage,
        'demand': demand,
        'supim': supim,
        'buy_sell_price': buy_sell_price,
        'dsm': dsm,
        'eff_factor': eff_factor
        }

    # sort nested indexes to make direct assignments work
    for key in data:
        if isinstance(data[key].index, pd.core.index.MultiIndex):
            data[key].sort_index(inplace=True)
    return data


# preparing the pyomo model
def pyomo_model_prep(data, timesteps):
    m = pyomo.ConcreteModel()

    # Preparations
    # ============
    # Data import. Syntax to access a value within equation definitions looks
    # like this:
    #
    #     m.storage.loc[site, storage, commodity][attribute]
    #
    m.global_prop = data['global_prop'].drop('description', axis=1)
    m.site = data['site']
    m.commodity = data['commodity']
    m.process = data['process']
    m.process_commodity = data['process_commodity']
    m.transmission = data['transmission']
    m.storage = data['storage']
    m.demand = data['demand']
    m.supim = data['supim']
    m.buy_sell_price = data['buy_sell_price']
    m.timesteps = timesteps
    m.dsm = data['dsm']
    m.eff_factor = data['eff_factor']

    # Converting Data frames to dict
    m.commodity_dict = m.commodity.to_dict()
    m.demand_dict = m.demand.to_dict()
    m.supim_dict = m.supim.to_dict()
    m.dsm_dict = m.dsm.to_dict()
    m.buy_sell_price_dict = m.buy_sell_price.to_dict()
    m.eff_factor_dict = m.eff_factor.to_dict()

    # process input/output ratios
    m.r_in = m.process_commodity.xs('In', level='Direction')['ratio']
    m.r_out = m.process_commodity.xs('Out', level='Direction')['ratio']
    m.r_in_dict = m.r_in.to_dict()
    m.r_out_dict = m.r_out.to_dict()

    # process areas
    m.proc_area = m.process['area-per-cap']
    m.sit_area = m.site['area']
    m.proc_area = m.proc_area[m.proc_area >= 0]
    m.sit_area = m.sit_area[m.sit_area >= 0]

    # input ratios for partial efficiencies
    # only keep those entries whose values are
    # a) positive and
    # b) numeric (implicitely, as NaN or NV compare false against 0)
    m.r_in_min_fraction = m.process_commodity.xs('In', level='Direction')
    m.r_in_min_fraction = m.r_in_min_fraction['ratio-min']
    m.r_in_min_fraction = m.r_in_min_fraction[m.r_in_min_fraction > 0]

    # output ratios for partial efficiencies
    # only keep those entries whose values are
    # a) positive and
    # b) numeric (implicitely, as NaN or NV compare false against 0)
    m.r_out_min_fraction = m.process_commodity.xs('Out', level='Direction')
    m.r_out_min_fraction = m.r_out_min_fraction['ratio-min']
    m.r_out_min_fraction = m.r_out_min_fraction[m.r_out_min_fraction > 0]

    # storages with fixed initial state
    m.stor_init_bound = m.storage['init']
    m.stor_init_bound = m.stor_init_bound[m.stor_init_bound >= 0]

    # derive annuity factor from WACC and depreciation duration
    m.process['annuity-factor'] = (m.process.apply(lambda x:
                                   annuity_factor(x['depreciation'],
                                                  x['wacc']),
                                   axis=1))
    m.transmission['annuity-factor'] = (m.transmission.apply(lambda x:
                                        annuity_factor(x['depreciation'],
                                                       x['wacc']),
                                        axis=1))
    m.storage['annuity-factor'] = (m.storage.apply(lambda x:
                                   annuity_factor(x['depreciation'],
                                                  x['wacc']),
                                   axis=1))

    # Converting Data frames to dictionaries
    #
    m.process_dict = m.process.to_dict()  # Changed
    m.transmission_dict = m.transmission.to_dict()  # Changed
    m.storage_dict = m.storage.to_dict()  # Changed
    return m


def split_columns(columns, sep='.'):
    """Split columns by separator into MultiIndex.

    Given a list of column labels containing a separator string (default: '.'),
    derive a MulitIndex that is split at the separator string.

    Args:
        columns: list of column labels, containing the separator string
        sep: the separator string (default: '.')

    Returns:
        a MultiIndex corresponding to input, with levels split at separator

    Example:
        >>> split_columns(['DE.Elec', 'MA.Elec', 'NO.Wind'])
        MultiIndex(levels=[['DE', 'MA', 'NO'], ['Elec', 'Wind']],
                   labels=[[0, 1, 2], [0, 0, 1]])

    """
    if len(columns) == 0:
        return columns
    column_tuples = [tuple(col.split('.')) for col in columns]
    return pd.MultiIndex.from_tuples(column_tuples)


def get_input(prob, name):
    """Return input DataFrame of given name from urbs instance.

    These are identical to the key names returned by function `read_excel`.
    That means they are lower-case names and use underscores for word
    separation, e.g. 'process_commodity'.

    Args:
        prob: a urbs model instance
        name: an input DataFrame name ('commodity', 'process', ...)

    Returns:
        the corresponding input DataFrame

    """
    if hasattr(prob, name):
        # classic case: input data DataFrames are accessible via named
        # attributes, e.g. `prob.process`.
        return getattr(prob, name)
    elif hasattr(prob, '_data') and name in prob._data:
        # load case: input data is accessible via the input data cache dict
        return prob._data[name]
    else:
        # unknown
        raise ValueError("Unknown input DataFrame name!")
