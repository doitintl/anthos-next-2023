async function capture() {
    try {
      const response = await fetch(`/capture`, {
        method: 'GET',
      });
      if (response.ok) {
        const text = await response.json();
        console.log(text);
        window.location.reload();
      }
      else {
        window.alert('Something went wrong... Please try again!');
      }
    } catch (err) {
      console.log(`Error when capturing image: ${err}`);
      window.alert('Something went wrong... Please try again!');
    }
}