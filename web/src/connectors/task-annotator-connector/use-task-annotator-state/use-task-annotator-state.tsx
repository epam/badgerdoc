import { useReducer } from 'react';
import { INITIAL_STATE } from './constants';
import { reducer } from './utils';

export const useTaskAnnotatorState = () => useReducer(reducer, INITIAL_STATE);
