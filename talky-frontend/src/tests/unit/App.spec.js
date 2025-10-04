import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import App from '../../App.vue';

describe('App.vue', () => {

  it('devrait afficher l\'écran de sélection initial au chargement', () => {
    const wrapper = mount(App);
    expect(wrapper.find('h1').exists()).toBe(true);
    expect(wrapper.find('h1').text()).toBe('Bienvenue ! 👋');
    expect(wrapper.find('.tile h3').text()).toBe('Talk-Show');
  });

  it('devrait passer à la vue formulaire après avoir cliqué sur un scénario', async () => {
    const wrapper = mount(App);
    await wrapper.find('.tile').trigger('click');
    const formContainer = wrapper.find('.form-container');
    expect(formContainer.exists()).toBe(true);
    expect(formContainer.find('h1').text()).toBe('Configurer : Talk-Show');
    const label = formContainer.find('.step-form label');
    expect(label.text()).toBe('Numéro');
  });

  it('devrait passer à l\'étape suivante après avoir soumis une étape du formulaire', async () => {
    const wrapper = mount(App);
    await wrapper.find('.tile').trigger('click');
    const formInput = wrapper.find('.step-form input');
    await formInput.setValue('9');
    const form = wrapper.find('.step-form');
    await form.trigger('submit');
    const nextLabel = wrapper.find('.step-form label');
    expect(nextLabel.text()).toBe('Thème');
    const activeStepLabel = wrapper.find('.step-item.is-active .step-label');
    expect(activeStepLabel.text()).toBe('Thème');
  });

});

